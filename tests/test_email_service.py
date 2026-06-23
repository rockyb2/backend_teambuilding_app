import unittest
from email import message_from_string
from unittest.mock import Mock, patch

from services.email_service import send_email, send_notification_email


SMTP_ENV = {
    "SMTP_ENABLED": "true",
    "SMTP_HOST": "smtp.example.test",
    "SMTP_PORT": "465",
    "SMTP_USERNAME": "smtp@ivoirtrips.com",
    "SMTP_PASSWORD": "secret",
    "SMTP_FROM_EMAIL": "notifications@ivoirtrips.com",
    "SMTP_NOTIFICATION_EMAIL": "crm@ivoirtrips.com",
    "SMTP_USE_SSL": "true",
}


class EmailServiceTests(unittest.TestCase):
    @patch.dict("os.environ", SMTP_ENV)
    @patch("services.email_service.smtplib.SMTP_SSL")
    def test_send_email_uses_requester_as_visible_sender_only(self, smtp_ssl_mock):
        server = Mock()
        smtp_ssl_mock.return_value.__enter__.return_value = server

        send_email(
            subject="Nouvelle demande contact - Test",
            body="Bonjour",
            to_emails=["crm@ivoirtrips.com"],
            sender_email="client@example.com",
            sender_name="Client Test",
            reply_to_email="client@example.com",
            reply_to_name="Client Test",
        )

        envelope_sender, recipients, raw_message = server.sendmail.call_args.args
        message = message_from_string(raw_message)

        self.assertEqual(envelope_sender, "notifications@ivoirtrips.com")
        self.assertEqual(recipients, ["crm@ivoirtrips.com"])
        self.assertEqual(message["From"], "Client Test <client@example.com>")
        self.assertEqual(message["Reply-To"], "Client Test <client@example.com>")

    @patch.dict("os.environ", SMTP_ENV)
    @patch("services.email_service.send_email")
    def test_notification_email_forwards_requester_sender(self, send_email_mock):
        send_notification_email(
            subject="Nouvelle demande",
            body="Bonjour",
            profile=None,
            sender_email="client@example.com",
            sender_name="Client Test",
        )

        send_email_mock.assert_called_once_with(
            subject="Nouvelle demande",
            body="Bonjour",
            html_body=None,
            to_emails=["crm@ivoirtrips.com"],
            profile=None,
            sender_email="client@example.com",
            sender_name="Client Test",
            reply_to_email="client@example.com",
            reply_to_name="Client Test",
        )


if __name__ == "__main__":
    unittest.main()
