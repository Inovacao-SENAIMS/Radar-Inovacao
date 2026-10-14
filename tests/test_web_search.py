import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("web_search", ROOT / "scripts" / "web_search.py")
ws = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ws)


def _make_response(payload):
    class _R:
        status = 200

        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return _R()


class ResolveProviderTests(unittest.TestCase):
    def test_auto_prefere_tavily_quando_ha_chave(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tv", "BRAVE_API_KEY": "bv"}, clear=False):
            self.assertEqual(ws.resolve_provider("auto"), ("tavily", "tv"))

    def test_auto_usa_brave_quando_so_ele_existe(self):
        env = {k: v for k, v in os.environ.items() if k not in ("TAVILY_API_KEY", "BRAVE_API_KEY")}
        env["BRAVE_API_KEY"] = "bv"
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(ws.resolve_provider("auto"), ("brave", "bv"))

    def test_auto_sem_chave_levanta_erro(self):
        env = {k: v for k, v in os.environ.items() if k not in ("TAVILY_API_KEY", "BRAVE_API_KEY")}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ws.SearchError):
                ws.resolve_provider("auto")

    def test_provider_desconhecido(self):
        with self.assertRaises(ws.SearchError):
            ws.resolve_provider("bing", "k")


class SearchTests(unittest.TestCase):
    def test_tavily_parseia_resultados(self):
        payload = {"results": [{"title": "T", "url": "https://a", "content": "S"}]}
        with patch.object(ws.urllib.request, "urlopen", return_value=_make_response(payload)):
            out = ws.search("q", provider="tavily", api_key="k")
        self.assertEqual(out, [{"title": "T", "url": "https://a", "snippet": "S"}])

    def test_brave_parseia_resultados(self):
        payload = {"web": {"results": [{"title": "T2", "url": "https://b", "description": "S2"}]}}
        with patch.object(ws.urllib.request, "urlopen", return_value=_make_response(payload)):
            out = ws.search("q", provider="brave", api_key="k")
        self.assertEqual(out, [{"title": "T2", "url": "https://b", "snippet": "S2"}])

    def test_build_context_tolera_falha_de_busca(self):
        with patch.object(ws, "search", side_effect=ws.SearchError("boom")):
            ctx = ws.build_context(["q1"], provider="tavily", api_key="k")
        self.assertIn("falha na busca", ctx)
        self.assertIn("q1", ctx)

    def test_build_context_monta_blocos(self):
        fake = [{"title": "T", "url": "https://a", "snippet": "S"}]
        with patch.object(ws, "search", return_value=fake):
            ctx = ws.build_context(["q1", "q2"], provider="tavily", api_key="k")
        self.assertIn("### Consulta: q1", ctx)
        self.assertIn("### Consulta: q2", ctx)
        self.assertIn("https://a", ctx)


if __name__ == "__main__":
    unittest.main()
