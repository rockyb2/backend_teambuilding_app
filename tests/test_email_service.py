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
    "SMTP_TEAMBUILDING_HOST": "smtp.zoho.test",
    "SMTP_TEAMBUILDING_PORT": "465",
    "SMTP_TEAMBUILDING_USERNAME": "teambuilding@ivoirtrips.com",
    "SMTP_TEAMBUILDING_PASSWORD": "team-secret",
    "SMTP_TEAMBUILDING_FROM_EMAIL": "teambuilding@ivoirtrips.com",
    "SMTP_TEAMBUILDING_NOTIFICATION_EMAIL": "teambuilding@ivoirtrips.com",
    "SMTP_TEAMBUILDING_USE_SSL": "true",
    "SMTP_CONTACT_HOST": "smtp.zoho.test",
    "SMTP_CONTACT_PORT": "465",
    "SMTP_CONTACT_USERNAME": "contact@ivoirtrips.com",
    "SMTP_CONTACT_PASSWORD": "contact-secret",
    "SMTP_CONTACT_FROM_EMAIL": "contact@ivoirtrips.com",
    "SMTP_CONTACT_NOTIFICATION_EMAIL": "contact@ivoirtrips.com",
    "SMTP_CONTACT_USE_SSL": "true",
    "SMTP_VOYAGE_HOST": "smtp.zoho.test",
    "SMTP_VOYAGE_PORT": "465",
    "SMTP_VOYAGE_USERNAME": "voyage@ivoirtrips.com",
    "SMTP_VOYAGE_PASSWORD": "voyage-secret",
    "SMTP_VOYAGE_FROM_EMAIL": "voyage@ivoirtrips.com",
    "SMTP_VOYAGE_NOTIFICATION_EMAIL": "voyage@ivoirtrips.com",
    "SMTP_VOYAGE_USE_SSL": "true",
    "SMTP_NEWSLETTER_HOST": "smtp.zoho.test",
    "SMTP_NEWSLETTER_PORT": "465",
    "SMTP_NEWSLETTER_USERNAME": "contact@ivoirtrips.com",
    "SMTP_NEWSLETTER_PASSWORD": "newsletter-secret",
    "SMTP_NEWSLETTER_FROM_EMAIL": "contact@ivoirtrips.com",
    "SMTP_NEWSLETTER_NOTIFICATION_EMAIL": "contact@ivoirtrips.com",
    "SMTP_NEWSLETTER_USE_SSL": "true",
}


class EmailServiceTests(unittest.TestCase):
    @patch.dict("os.environ", SMTP_ENV)
    @patch("services.email_service.smtplib.SMTP_SSL")
    def test_notifications_use_profile_sender_and_requester_reply_to(self, smtp_ssl_mock):
        server = Mock()
        smtp_ssl_mock.return_value.__enter__.return_value = server

        profiles = {
            "CONTACT": "contact@ivoirtrips.com",
            "TEAMBUILDING": "teambuilding@ivoirtrips.com",
            "VOYAGE": "voyage@ivoirtrips.com",
            "NEWSLETTER": "contact@ivoirtrips.com",
        }

        for profile, mailbox in profiles.items():
            with self.subTest(profile=profile):
                server.reset_mock()
                send_email(
                    subject="Nouvelle demande - Test",
                    body="Bonjour",
                    to_emails=[mailbox],
                    profile=profile,
                    sender_email="client@example.com",
                    sender_name="Client Test",
                    reply_to_email="client@example.com",
                    reply_to_name="Client Test",
                )

                envelope_sender, recipients, raw_message = server.sendmail.call_args.args
                message = message_from_string(raw_message)

                self.assertEqual(envelope_sender, mailbox)
                self.assertEqual(recipients, [mailbox])
                self.assertEqual(message["From"], f"Client Test <{mailbox}>")
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
