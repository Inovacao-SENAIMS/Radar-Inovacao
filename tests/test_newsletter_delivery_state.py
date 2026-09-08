"""Contract checks for newsletter delivery state kept by Apps Script."""

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "send_newsletter", ROOT / "scripts" / "send_newsletter.py"
)
send_newsletter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(send_newsletter)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class NewsletterDeliveryStateTests(unittest.TestCase):
    cfg = {"webapp_url": "https://example.test/exec"}
    key = "test-key"

    def test_reads_delivered_emails_for_the_current_edition(self):
        with patch.object(send_newsletter, "urlopen", return_value=_Response({"emails": ["Ana@Example.test"]})) as opened:
            delivered = send_newsletter.fetch_delivered_emails(self.cfg, self.key, "2026-09-08")

        self.assertEqual(delivered, {"ana@example.test"})
        self.assertIn("action=sent", opened.call_args.args[0].full_url)
        self.assertIn("edition=2026-09-08", opened.call_args.args[0].full_url)

    def test_records_a_successful_delivery_in_the_remote_state(self):
        with patch.object(send_newsletter, "urlopen", return_value=_Response({"ok": True})) as opened:
            send_newsletter.record_delivery(self.cfg, self.key, "2026-09-08", "ana@example.test")

        self.assertIn("action=record_sent", opened.call_args.args[0].full_url)
        self.assertIn("email=ana%40example.test", opened.call_args.args[0].full_url)

    def test_apps_script_requires_confirmation_before_listing_a_subscriber(self):
        source = (ROOT / "scripts" / "google" / "appsscript_subscribers.gs").read_text(encoding="utf-8")
        self.assertIn("'pendente', token", source)
        self.assertIn("sendConfirmation_(nome, email, token)", source)

    def test_parser_classifies_federal_institutes_as_icts(self):
        parser_spec = importlib.util.spec_from_file_location(
            "md_to_json", ROOT / "scripts" / "md_to_json.py"
        )
        parser = importlib.util.module_from_spec(parser_spec)
        parser_spec.loader.exec_module(parser)
        text = """## Tabela de Editais\n\n| Edital | Fonte | Status | Abertura | Encerramento | Dias restantes | Público-alvo | Valor/Faixa | Contrapartida | Principais exigências | Link |\n|---|---|---|---|---|---|---|---|---|---|---|\n| Teste | Fonte | Aberto | 01/09/2026 | 30/09/2026 | 22 | Institutos Federais de Educação, Ciência e Tecnologia | — | — | — | https://example.test |\n"""
        self.assertEqual(parser.parse_markdown(text)["editais"][0]["tipo_publico"], "ICT")


if __name__ == "__main__":
    unittest.main()
