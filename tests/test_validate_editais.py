import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_editais", ROOT / "scripts" / "validate_editais.py")
ve = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ve)


def _edital(name, status="aberto", link="https://ok.test"):
    return {"edital": name, "fonte": "F", "status": status, "abertura": "01/01/2026",
            "encerramento": "01/12/2026", "publico": "Empresas", "valor": "R$ 1",
            "contrapartida": "—", "exigencias": "—", "link": link}


def _payload(n=12, **over):
    data = {"editais": [_edital(f"E{i}") for i in range(n)],
            "aderencia": [], "nao_confirmado": [], "resumo_executivo": ["x"], "alerta_prazo": "x"}
    data.update(over)
    return data


class ValidateTests(unittest.TestCase):
    def test_payload_valido_passa(self):
        ve.validate(_payload(), previous=None, min_editais=10)

    def test_poucos_editais_falha(self):
        with self.assertRaises(ve.ValidationError):
            ve.validate(_payload(3), previous=None, min_editais=10)

    def test_status_invalido_falha(self):
        data = _payload()
        data["editais"][0]["status"] = "talvez"
        with self.assertRaises(ve.ValidationError):
            ve.validate(data, previous=None, min_editais=10)

    def test_link_sem_http_falha(self):
        data = _payload()
        data["editais"][0]["link"] = "ftp://x"
        with self.assertRaises(ve.ValidationError):
            ve.validate(data, previous=None, min_editais=10)

    def test_placeholder_falha(self):
        data = _payload()
        data["editais"][0]["valor"] = "TODO"
        with self.assertRaises(ve.ValidationError):
            ve.validate(data, previous=None, min_editais=10)

    def test_queda_maior_que_30_por_cento_falha(self):
        previous = {"editais": [_edital(f"E{i}") for i in range(20)]}
        with self.assertRaises(ve.ValidationError):
            ve.validate(_payload(12), previous=previous, min_editais=10)


if __name__ == "__main__":
    unittest.main()
