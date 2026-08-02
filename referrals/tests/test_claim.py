from django.test import TestCase
from django.urls import reverse

from referrals.models import ReferralAttribution, ReferralProfile
from referrals.services import claim_referral, get_or_create_profile


class ReferralClaimTests(TestCase):
    def test_claim_grants_rewards(self):
        referrer, _ = get_or_create_profile("device-referrer")
        result = claim_referral("device-referee", referrer.referral_code)

        referrer.refresh_from_db()
        referee = ReferralProfile.objects.get(device_id="device-referee")

        self.assertEqual(referrer.credits, 10)
        self.assertEqual(referrer.vip_days, 1)
        self.assertEqual(referee.credits, 5)
        self.assertEqual(
            ReferralAttribution.objects.filter(status="rewarded").count(), 1
        )
        self.assertEqual(result["rewards"]["referrer_vip_days"], 1)

    def test_cannot_claim_twice(self):
        referrer, _ = get_or_create_profile("device-a")
        claim_referral("device-b", referrer.referral_code)
        from referrals.services import ReferralError

        with self.assertRaises(ReferralError):
            claim_referral("device-b", referrer.referral_code)

    def test_me_and_claim_api(self):
        me_url = reverse("referral-me")
        created = self.client.post(
            me_url, data={"device_id": "api-ref"}, content_type="application/json"
        )
        self.assertIn(created.status_code, (200, 201))
        code = created.json()["code"]

        claim_url = reverse("referral-claim")
        claimed = self.client.post(
            claim_url,
            data={"device_id": "api-new", "referral_code": code},
            content_type="application/json",
        )
        self.assertEqual(claimed.status_code, 201)
        self.assertEqual(claimed.json()["referrer"]["credits"], 10)
