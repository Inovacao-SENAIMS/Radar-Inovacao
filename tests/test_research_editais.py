import importlib.util
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "gemini_response.json"
SPEC = importlib.util.spec_from_file_location("research_editais", ROOT / "scripts" / "research_editais.py")
re_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(re_mod)


class OfflineRunTests(unittest.TestCase):
    def test_offline_gera_json_js_e_md_validos(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out_json, out_js = tmp / "editais.json", tmp / "editais.js"
            result = re_mod.run(
                date(2026, 10, 8),
                base_path=tmp / "none.json",
                out_json=out_json, out_js=out_js, md_dir=tmp,
                offline=FIX, model="x", api_key="", dry_run=False, min_editais=10,
            )
            self.assertTrue(out_json.exists())
            self.assertTrue(out_js.exists())
            self.assertEqual(len(result["editais"]), 12)
            self.assertEqual(result["meta"]["reference_date"], "2026-10-08")
            self.assertEqual(result["stats"]["continuos"], 2)
            md_files = list(tmp.glob("Monitoramento_Editais_Inovacao_2026-10-08.md"))
            self.assertEqual(len(md_files), 1)
            self.assertTrue(out_js.read_text(encoding="utf-8").startswith("window.EDITAIS_DATA = "))

    def test_offline_invalido_nao_escreve_arquivos(self):
        bad = json.loads(FIX.read_text(encoding="utf-8"))
        bad["editais"] = bad["editais"][:3]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            badfile = tmp / "bad.json"
            badfile.write_text(json.dumps(bad), encoding="utf-8")
            out_json = tmp / "editais.json"
            with self.assertRaises(Exception):
                re_mod.run(date(2026, 10, 8), base_path=tmp / "none.json",
                           out_json=out_json, out_js=tmp / "editais.js", md_dir=tmp,
                           offline=badfile, model="x", api_key="", dry_run=False, min_editais=10)
            self.assertFalse(out_json.exists())


class GroqProviderTests(unittest.TestCase):
    def test_provider_groq_usa_busca_e_gera_json_js_md(self):
        payload = json.loads(FIX.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with patch.object(re_mod.ws, "resolve_provider", return_value=("tavily", "k")), \
                 patch.object(re_mod.ws, "build_context", return_value="### Consulta: x\n- a — https://a") as fake_ctx, \
                 patch.object(re_mod.gq, "generate", return_value=payload) as fake_gen:
                result = re_mod.run(
                    date(2026, 10, 8),
                    base_path=tmp / "none.json",
                    out_json=tmp / "editais.json", out_js=tmp / "editais.js", md_dir=tmp,
                    provider="groq", model="openai/gpt-oss-120b", api_key="k",
                    dry_run=False, min_editais=10,
                )
            self.assertTrue((tmp / "editais.json").exists())
            self.assertTrue((tmp / "editais.js").exists())
            self.assertEqual(len(result["editais"]), 12)
            fake_ctx.assert_called_once()
            fake_gen.assert_called_once()


class ChunkedGroqTests(unittest.TestCase):
    def test_merge_deduplica_por_nome(self):
        p1 = {"editais": [{"edital": "A", "status": "aberto", "link": "https://a"},
                          {"edital": "B", "status": "aberto", "link": "https://b"}],
              "aderencia": [{"edital": "A"}], "nao_confirmado": []}
        p2 = {"editais": [{"edital": "b", "status": "aberto", "link": "https://b"},
                          {"edital": "C", "status": "aberto", "link": "https://c"}],
              "aderencia": [{"edital": "B"}, {"edital": "C"}], "nao_confirmado": []}
        merged = re_mod._merge_chunk_payloads([p1, p2])
        self.assertEqual([e["edital"] for e in merged["editais"]], ["A", "B", "C"])
        self.assertEqual(len(merged["aderencia"]), 3)

    def test_normaliza_campos_com_nomes_do_modelo(self):
        payload = {"editais": [{
            "nome": "E1", "fonte": "X", "status": "Fluxo contínuo",
            "publico_alvo": "ICTs", "valor_faixa": "R$ 1 mi",
            "principais_exigencias": "SAGe", "link": "https://a",
            "aderencia": {"grau": "alta", "institutos": "ISI Biomassa"},
        }]}
        merged = re_mod._merge_chunk_payloads([payload])
        e = merged["editais"][0]
        self.assertEqual(e["edital"], "E1")
        self.assertEqual(e["status"], "continuo")
        self.assertEqual(e["valor"], "R$ 1 mi")
        self.assertEqual(e["exigencias"], "SAGe")
        self.assertEqual(merged["aderencia"][0]["grau"], "alta")
        self.assertEqual(merged["aderencia"][0]["edital"], "E1")

    def test_synthesize_summary_gera_resumo_e_alerta(self):
        payload = {"editais": [{"edital": "X", "status": "aberto", "encerramento": "15/10/2026"}],
                   "nao_confirmado": [{"edital": "Y"}], "aderencia": []}
        out = re_mod._synthesize_summary(payload, date(2026, 10, 8))
        self.assertTrue(out["resumo_executivo"])
        self.assertIn("X", out["alerta_prazo"])

    def test_chunked_run_gera_json_js_md(self):
        payload = json.loads(FIX.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with patch.object(re_mod.ws, "resolve_provider", return_value=("tavily", "k")), \
                 patch.object(re_mod.ws, "build_context", return_value="ctx"), \
                 patch.object(re_mod.ws, "chunk_groups",
                              return_value=[("g1", ["q1"]), ("g2", ["q2"])]), \
                 patch.object(re_mod, "_groq_generate", return_value=payload), \
                 patch.object(re_mod.time, "sleep", return_value=None):
                result = re_mod.run(
                    date(2026, 10, 8),
                    base_path=tmp / "none.json",
                    out_json=tmp / "editais.json", out_js=tmp / "editais.js", md_dir=tmp,
                    provider="groq", model="m", api_key="k", chunk=True,
                    dry_run=False, min_editais=10,
                )
            self.assertTrue((tmp / "editais.json").exists())
            self.assertTrue((tmp / "editais.js").exists())
            self.assertEqual(len(result["editais"]), 12)


if __name__ == "__main__":
    unittest.main()
