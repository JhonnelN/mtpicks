import hashlib
import hmac
import json

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from integrations.dispatcher import sign_payload
from integrations.models import WebhookEndpoint
from racing.odds import parse_odds_to_decimal, synthetic_mtp5_odds
from decimal import Decimal


class SignPayloadTests(SimpleTestCase):
    def test_hmac_signature(self):
        body = b'{"event":"race.next"}'
        secret = "super-secret"
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        self.assertEqual(sign_payload(secret, body), expected)


class OddsParseTests(SimpleTestCase):
    def test_fractional_odds(self):
        self.assertEqual(parse_odds_to_decimal("5/2"), Decimal("3.5"))
        self.assertEqual(parse_odds_to_decimal("EVEN"), Decimal("2.0"))

    def test_synthetic_shortens(self):
        morning = parse_odds_to_decimal("5/1")
        mtp = parse_odds_to_decimal(synthetic_mtp5_odds("5/1"))
        self.assertIsNotNone(morning)
        self.assertIsNotNone(mtp)
        self.assertLess(mtp, morning)


@override_settings(TELEGRAM_ENABLED=False)
class WebhookApiTests(TestCase):
    def test_create_webhook_requires_admin_token(self):
        url = reverse("webhook-endpoint-list")
        response = self.client.post(
            url,
            data=json.dumps(
                {
                    "name": "Partner",
                    "url": "https://example.com/hook",
                    "secret": "abc123",
                    "events": ["race.official"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_create_webhook_with_token(self):
        url = reverse("webhook-endpoint-list")
        response = self.client.post(
            url,
            data=json.dumps(
                {
                    "name": "Partner",
                    "url": "https://example.com/hook",
                    "secret": "abc123",
                    "events": ["race.official"],
                }
            ),
            content_type="application/json",
            HTTP_X_ADMIN_TOKEN="dev-admin-token",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WebhookEndpoint.objects.count(), 1)
