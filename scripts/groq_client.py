#!/usr/bin/env python3
"""groq_client.py — wrapper mínimo da API do Groq (compatível com OpenAI).

Por que um User-Agent explícito: o Cloudflare na frente da api.groq.com
bloqueia o agente padrão do Python (``Python-urllib/3.x``) com
``HTTP 403 - error code 1010``. Sem um UA "de navegador", toda chamada falha.

API compatível com OpenAI (``/openai/v1/chat/completions``). O modo JSON usa
``response_format={"type": "json_object"}`` — o prompt precisa conter a palavra
"JSON". Não há *schema* nativo como no Gemini; a validação é feita depois por
``validate_editais.py``.
"""
import json
import re
import urllib.error
import urllib.request

API_BASE = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"
# Cloudflare bloqueia o UA padrão do urllib (HTTP 403 / error code 1010).
USER_AGENT = "curl/8.7.1"

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)
_JSON_LOOSE = re.compile(r"\{.*\}", re.S)


class GroqError(RuntimeError):
    pass


def build_request_body(prompt, model, json_mode=True, temperature=0, max_tokens=None,
                       reasoning_effort=None):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    if max_tokens:
        body["max_tokens"] = max_tokens
    if reasoning_effort:
        # gpt-oss: reduz os tokens de "raciocínio" e libera orçamento para o JSON final.
        body["reasoning_effort"] = reasoning_effort
    return body


def extract_text(response_json):
    try:
        return response_json["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise GroqError(f"resposta sem choices/message: {exc}") from exc


def extract_json(text):
    m = _JSON_BLOCK.search(text) or _JSON_LOOSE.search(text)
    if not m:
        raise GroqError("nenhum JSON encontrado na resposta")
    try:
        return json.loads(m.group(1) if m.re is _JSON_BLOCK else m.group(0))
    except json.JSONDecodeError as exc:
        raise GroqError(f"JSON inválido: {exc}") from exc


class _HttpError(GroqError):
    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(f"HTTP {code}: {detail[:300]}")


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


def _post(url, body, timeout, headers):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise _HttpError(exc.code, detail) from exc
    except urllib.error.URLError as exc:
        raise GroqError(f"falha de rede ao chamar o Groq: {exc}") from exc


def generate(prompt, *, model=DEFAULT_MODEL, api_key, json_mode=True, temperature=0,
             max_tokens=None, reasoning_effort=None, timeout=180):
    if not api_key:
        raise GroqError("GROQ_API_KEY ausente")
    url = f"{API_BASE}/chat/completions"
    body = build_request_body(prompt, model, json_mode=json_mode, temperature=temperature,
                              max_tokens=max_tokens, reasoning_effort=reasoning_effort)
    resp = _post(url, body, timeout, _headers(api_key))
    text = extract_text(resp)
    if json_mode:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return extract_json(text)
    return extract_json(text)


def list_models(*, api_key, timeout=60):
    if not api_key:
        raise GroqError("GROQ_API_KEY ausente")
    req = urllib.request.Request(f"{API_BASE}/models", headers=_headers(api_key), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise _HttpError(exc.code, exc.read().decode("utf-8", "replace")) from exc
    return sorted(m["id"] for m in payload.get("data", []))
