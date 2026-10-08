import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("research_prompt", ROOT / "scripts" / "research_prompt.py")
rp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rp)


class PromptTests(unittest.TestCase):
    base = {"editais": [{"edital": "Edital Antigo", "fonte": "FAPESP",
                         "status": "aberto", "encerramento": "10/10/2026", "link": "https://a.test"}]}

    def test_inclui_data_base_e_metodologia(self):
        out = rp.build(self.base, "2026-10-08", "Use fontes oficiais.")
        self.assertIn("2026-10-08", out)
        self.assertIn("Edital Antigo", out)
        self.assertIn("Use fontes oficiais.", out)

    def test_proibe_invencao_e_nao_pede_campos_calculados(self):
        out = rp.build(self.base, "2026-10-08", "Metodologia.").lower()
        self.assertIn("não invente", out)
        self.assertIn("não inclua campos calculados", out)
        self.assertNotIn("quantos editais", out)

    def test_schema_exige_campos_essenciais(self):
        props = rp.RESPONSE_SCHEMA["properties"]
        self.assertEqual(set(props), {"editais", "aderencia", "nao_confirmado",
                                      "resumo_executivo", "alerta_prazo"})
        edital_props = props["editais"]["items"]["properties"]
        for field in ("edital", "fonte", "status", "abertura", "encerramento",
                      "publico", "valor", "contrapartida", "exigencias", "link"):
            self.assertIn(field, edital_props)


if __name__ == "__main__":
    unittest.main()
