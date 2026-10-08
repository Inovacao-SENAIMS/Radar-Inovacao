import importlib.util
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
