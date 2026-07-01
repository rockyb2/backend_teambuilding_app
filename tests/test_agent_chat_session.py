import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.env_loader import load_local_env

load_local_env()

from api.agent.routes import ChatRequest, chat_with_agent_endpoint


class AgentChatSessionTests(unittest.TestCase):
    @patch("api.agent.routes.chat_with_agent", return_value="Reponse agent")
    @patch("api.agent.routes.crud_chat")
    def test_chat_endpoint_persists_session_and_passes_history(self, crud_chat_mock, chat_mock):
        db = Mock()
        crud_chat_mock.get_or_create_session.return_value = SimpleNamespace(id=7)
        crud_chat_mock.get_recent_messages.return_value = [
            SimpleNamespace(role="user", content="Bonjour"),
            SimpleNamespace(role="assistant", content="Quel est votre nom ?"),
        ]

        response = chat_with_agent_endpoint(
            ChatRequest(
                message="Je m'appelle Awa",
                session_id="session-123",
                locale="fr",
            ),
            db,
        )

        self.assertEqual(response["session_id"], "session-123")
        self.assertEqual(response["content"], "Reponse agent")
        chat_mock.assert_called_once_with(
            "Je m'appelle Awa",
            conversation_history=[
                {"role": "user", "content": "Bonjour"},
                {"role": "assistant", "content": "Quel est votre nom ?"},
            ],
        )
        self.assertEqual(crud_chat_mock.add_message.call_count, 2)


if __name__ == "__main__":
    unittest.main()
