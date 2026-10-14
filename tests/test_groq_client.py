import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("groq_client", ROOT / "scripts" / "groq_client.py")
gq = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gq)


def _make_response(text):
    payload = {"choices": [{"message": {"content": text}}]}

    class _R:
        status = 200

        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return _R()


class GroqClientTests(unittest.TestCase):
    def test_body_modo_json(self):
        body = gq.build_request_body("responda em JSON", "openai/gpt-oss-120b")
        self.assertEqual(body["model"], "openai/gpt-oss-120b")
        self.assertEqual(body["messages"][0]["content"], "responda em JSON")
        self.assertEqual(body["response_format"], {"type": "json_object"})

    def test_body_sem_modo_json(self):
        body = gq.build_request_body("oi", "m", json_mode=False)
        self.assertNotIn("response_format", body)

    def test_extract_text_e_json(self):
        self.assertEqual(gq.extract_text({"choices": [{"message": {"content": "ab"}}]}), "ab")
        self.assertEqual(gq.extract_json('```json\n{"a": "1"}\n```'), {"a": "1"})
        self.assertEqual(gq.extract_json('bla {"a": "2"} bla'), {"a": "2"})
        with self.assertRaises(gq.GroqError):
            gq.extract_json("sem json")

    def test_generate_exige_api_key(self):
        with self.assertRaises(gq.GroqError):
            gq.generate("oi", api_key="")

    def test_generate_envia_user_agent_e_authorization(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["ua"] = req.get_header("User-agent")
            captured["auth"] = req.get_header("Authorization")
            return _make_response('{"a": "1"}')

        with patch.object(gq.urllib.request, "urlopen", side_effect=fake_urlopen):
            out = gq.generate("oi", model="m", api_key="segredo")
        self.assertEqual(out, {"a": "1"})
        self.assertEqual(captured["ua"], gq.USER_AGENT)
        self.assertEqual(captured["auth"], "Bearer segredo")

    def test_generate_faz_fallback_de_bloco_cercado(self):
        with patch.object(gq.urllib.request, "urlopen", return_value=_make_response('```json\n{"a": "2"}\n```')):
            out = gq.generate("oi", model="m", api_key="k")
        self.assertEqual(out, {"a": "2"})


if __name__ == "__main__":
    unittest.main()
