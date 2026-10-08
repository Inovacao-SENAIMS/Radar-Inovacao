import importlib.util
from datetime import date
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("monitor_report", ROOT / "scripts" / "monitor_report.py")
mr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mr)


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ComputeTests(unittest.TestCase):
    today = date(2026, 10, 8)

    def test_dias_converte_deadline_em_dias_restantes(self):
        item = {"status": "aberto", "encerramento": "12/10/2026"}
        self.assertEqual(mr.compute_dias(item, self.today), "4")

    def test_dias_hoje(self):
        item = {"status": "aberto", "encerramento": "08/10/2026"}
        self.assertEqual(mr.compute_dias(item, self.today), "0 (hoje)")

    def test_continuo_e_sem_data_retornam_travessao(self):
        self.assertEqual(mr.compute_dias({"status": "continuo", "encerramento": "Contínuo"}, self.today), "—")
        self.assertEqual(mr.compute_dias({"status": "aberto", "encerramento": "Não encontrado"}, self.today), "—")

    def test_stats_contam_status_e_encerram_7d(self):
        editais = [
            {"status": "aberto", "encerramento": "10/10/2026"},
            {"status": "aberto", "encerramento": "30/11/2026"},
            {"status": "continuo", "encerramento": "Contínuo"},
            {"status": "breve", "encerramento": "26/11/2026"},
        ]
        self.assertEqual(
            mr.compute_stats(editais, self.today),
            {"abertos": 2, "continuos": 1, "em_breve": 1, "encerram_7d": 1, "nao_confirmado": 0},
        )


class DiffTests(unittest.TestCase):
    def test_classifica_novo_encerrado_e_prazo_alterado(self):
        previous = {"editais": [
            {"edital": "A", "fonte": "F1", "encerramento": "10/10/2026", "valor": "X"},
            {"edital": "B", "fonte": "F2", "encerramento": "01/11/2026", "valor": "Y"},
        ]}
        current = {"editais": [
            {"edital": "A", "fonte": "F1", "encerramento": "20/10/2026", "valor": "X"},
            {"edital": "C", "fonte": "F3", "encerramento": "05/12/2026", "valor": "Z"},
        ]}
        out = mr.diff_novidades(previous, current)
        self.assertEqual([x["Edital"] for x in out["novos_editais"]], ["C"])
        self.assertEqual([x["Edital"] for x in out["editais_encerrados"]], ["B"])
        self.assertEqual([x["Edital"] for x in out["alteracoes_prazo"]], ["A"])

    def test_sem_mudanca_retorna_listas_vazias(self):
        base = {"editais": [{"edital": "A", "fonte": "F", "encerramento": "10/10/2026", "valor": "X"}]}
        out = mr.diff_novidades(base, base)
        self.assertEqual((out["novos_editais"], out["editais_encerrados"], out["alteracoes_prazo"]), ([], [], []))


class BuildMarkdownTests(unittest.TestCase):
    today = date(2026, 10, 8)

    def _sample(self):
        return {
            "editais": [
                {"edital": "Edital A", "fonte": "FAPESP", "status": "aberto", "abertura": "01/09/2026",
                 "encerramento": "12/10/2026", "publico": "Empresas", "valor": "R$ 1 mi",
                 "contrapartida": "Não exige", "exigencias": "SAGe", "link": "https://a.test"},
                {"edital": "Edital B", "fonte": "CNPq", "status": "continuo", "abertura": "Permanente",
                 "encerramento": "Contínuo", "publico": "ICTs", "valor": "—",
                 "contrapartida": "—", "exigencias": "—", "link": "https://b.test"},
            ],
            "aderencia": [
                {"edital": "Edital A", "institutos": "ISI Biomassa", "grau": "alta",
                 "foco_educacional": "Não", "justificativa": "Bioenergia."},
            ],
            "nao_confirmado": [{"edital": "Edital X", "fonte": "FGB", "motivo": "Sem data."}],
            "resumo_executivo": ["Abertos agora: 1 edital; 1 de fluxo contínuo."],
            "alerta_prazo": "Edital A (12/10/2026).",
        }

    def test_round_trip_mantem_contagem(self):
        parser = _load("md_to_json", "scripts/md_to_json.py")
        data = self._sample()
        md = mr.build_markdown(data, self.today, previous={"editais": []},
                               scope="Nacional e internacional.", methodology="Fontes oficiais.")
        parsed = parser.parse_markdown(md)
        self.assertEqual(len(parsed["editais"]), 2)
        self.assertEqual(len(parsed["aderencia"]), 1)
        self.assertEqual(len(parsed["nao_confirmado"]), 1)
        self.assertEqual(parsed["meta"]["reference_date"], "2026-10-08")
        self.assertEqual(parsed["stats"]["abertos"], 1)
        self.assertEqual(parsed["stats"]["continuos"], 1)
        self.assertIn("Edital A", parsed["alerta_prazo"])
        self.assertEqual(len(parsed["novidades"]["novos_editais"]), 2)

    def test_ranges_do_markdown_sao_respeitados(self):
        md = mr.build_markdown(self._sample(), self.today, previous={"editais": []},
                               scope="Nacional.", methodology="Fontes oficiais.")
        for section in ("## Resumo Executivo", "## Tabela de Editais",
                        '## Editais "Não confirmado"', "## Aderência com os institutos SENAI/MS",
                        "## Novidades desde"):
            self.assertIn(section, md)


if __name__ == "__main__":
    unittest.main()
