import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gemini_client", ROOT / "scripts" / "gemini_client.py")
gc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gc)

SCHEMA = {"type": "OBJECT", "properties": {"a": {"type": "STRING"}}, "required": ["a"]}


class GeminiClientTests(unittest.TestCase):
    def test_body_com_schema_e_busca(self):
        body = gc.build_request_body("oi", SCHEMA, use_search=True)
        self.assertEqual(body["contents"][0]["parts"][0]["text"], "oi")
        self.assertEqual(body["tools"], [{"google_search": {}}])
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertIn("responseSchema", body["generationConfig"])

    def test_body_sem_schema_nao_tem_generation_config(self):
        body = gc.build_request_body("oi", None, use_search=False)
        self.assertNotIn("generationConfig", body)
        self.assertNotIn("tools", body)

    def test_extract_text_concatena_parts(self):
        resp = {"candidates": [{"content": {"parts": [{"text": "a"}, {"text": "b"}]}}]}
        self.assertEqual(gc.extract_text(resp), "ab")

    def test_extract_json_de_bloco_cercado_e_de_texto_puro(self):
        self.assertEqual(gc.extract_json('```json\n{"a": "1"}\n```'), {"a": "1"})
        self.assertEqual(gc.extract_json('texto antes {"a": "2"} depois'), {"a": "2"})
        with self.assertRaises(gc.GeminiError):
            gc.extract_json("sem json aqui")


def _make_response(text):
    payload = {"candidates": [{"content": {"parts": [{"text": text}]}}]}

    class _R:
        status = 200

        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return _R()


def _http_400(detail):
    return gc.urllib.error.HTTPError(
        "https://x", 400, "Bad Request", {}, io.BytesIO(detail.encode("utf-8"))
    )


class GenerateTests(unittest.TestCase):
    def test_generate_retorna_json_quando_schema(self):
        with patch.object(gc.urllib.request, "urlopen", return_value=_make_response('{"a": "1"}')):
            out = gc.generate("oi", model="gemini-2.5-flash", api_key="k", schema=SCHEMA)
        self.assertEqual(out, {"a": "1"})

    def test_generate_faz_fallback_quando_400_com_schema(self):
        calls = {"n": 0}

        def fake_urlopen(req, timeout=None, context=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _http_400("responseSchema and tools are incompatible")
            return _make_response('```json\n{"a": "2"}\n```')

        with patch.object(gc.urllib.request, "urlopen", side_effect=fake_urlopen):
            out = gc.generate("oi", model="gemini-2.5-flash", api_key="k", schema=SCHEMA)
        self.assertEqual(out, {"a": "2"})
        self.assertEqual(calls["n"], 2)

    def test_generate_sem_api_key_levanta_erro(self):
        with self.assertRaises(gc.GeminiError):
            gc.generate("oi", model="m", api_key="")


if __name__ == "__main__":
    unittest.main()
