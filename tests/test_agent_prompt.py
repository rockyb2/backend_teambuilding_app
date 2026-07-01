import unittest

from agentautomatisation.agentcore import AGENT_INSTRUCTIONS, SALES_EMAIL


class AgentPromptTests(unittest.TestCase):
    def test_prompt_matches_current_public_site_and_crm_scope(self):
        expected_sections = [
            "Team building",
            "Tourisme et voyages",
            "Evenements signature",
            "Evenements entreprise et MICE",
            "Studio Mossika",
            "Contact et newsletter",
            "chat_sessions/chat_messages",
            "/api/demandes-team-building",
            "/api/demandes-tourisme/custom",
            "proformas tourisme",
            "Production CRM",
        ]

        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, AGENT_INSTRUCTIONS)

    def test_prompt_keeps_structured_payload_contract(self):
        self.assertIn('"client"', AGENT_INSTRUCTIONS)
        self.assertIn('"demande"', AGENT_INSTRUCTIONS)
        self.assertIn("type_demande", AGENT_INSTRUCTIONS)
        self.assertIn("points_manquants", AGENT_INSTRUCTIONS)

    def test_sales_report_recipient_is_contact_address(self):
        self.assertEqual(SALES_EMAIL, "contact@ivoirtrips.com")
        self.assertIn("contact@ivoirtrips.com", AGENT_INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
