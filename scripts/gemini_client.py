#!/usr/bin/env python3
"""gemini_client.py — wrapper mínimo da API Gemini (stdlib) com fallback sem schema."""
import json
import re
import urllib.error
import urllib.request
from urllib.parse import quote

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)
_JSON_LOOSE = re.compile(r"\{.*\}", re.S)


class GeminiError(RuntimeError):
    pass


def build_request_body(prompt, schema, use_search):
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if use_search:
        body["tools"] = [{"google_search": {}}]
    if schema:
        body["generationConfig"] = {"responseMimeType": "application/json", "responseSchema": schema}
    return body


def extract_text(response_json):
    try:
        parts = response_json["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError(f"resposta sem candidates/content/parts: {exc}") from exc
    return "".join(p.get("text", "") for p in parts)


def extract_json(text):
    m = _JSON_BLOCK.search(text) or _JSON_LOOSE.search(text)
    if not m:
        raise GeminiError("nenhum JSON encontrado na resposta")
    try:
        return json.loads(m.group(1) if m.re is _JSON_BLOCK else m.group(0))
    except json.JSONDecodeError as exc:
        raise GeminiError(f"JSON inválido: {exc}") from exc


class _HttpError(GeminiError):
    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(f"HTTP {code}: {detail[:300]}")


def _post(url, body, timeout):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise _HttpError(exc.code, detail) from exc
    except urllib.error.URLError as exc:
        raise GeminiError(f"falha de rede ao chamar o Gemini: {exc}") from exc


def generate(prompt, *, model, api_key, schema=None, use_search=True, timeout=120, _post=_post):
    if not api_key:
        raise GeminiError("GEMINI_API_KEY ausente")
    url = f"{API_BASE}/{quote(model)}:generateContent?key={quote(api_key)}"
    try:
        resp = _post(url, build_request_body(prompt, schema, use_search), timeout)
    except _HttpError as exc:
        if schema and use_search and exc.code == 400 and "schema" in exc.detail.lower():
            resp = _post(url, build_request_body(prompt, None, use_search), timeout)
        else:
            raise
    text = extract_text(resp)
    if schema:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return extract_json(text)
    return extract_json(text)
