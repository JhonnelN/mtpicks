"""Lightweight referral profiles with credits / VIP days (no JWT auth)."""

from __future__ import annotations

import secrets
import string

from django.db import models
from django.utils import timezone


def generate_referral_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"AHR{token}"


class ReferralProfile(models.Model):
    """Device-linked VIP profile that holds referral code and rewards."""

    device_id = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField(blank=True)
    referral_code = models.CharField(max_length=16, unique=True, db_index=True)
    credits = models.PositiveIntegerField(default=0)
    vip_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.referral_code} ({self.device_id[:12]})"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            for _ in range(10):
                code = generate_referral_code()
                if not ReferralProfile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)


class ReferralAttribution(models.Model):
    """One referee profile can be attributed to a single referrer."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUALIFIED = "qualified", "Qualified"
        REWARDED = "rewarded", "Rewarded"

    referrer = models.ForeignKey(
        ReferralProfile, on_delete=models.CASCADE, related_name="referrals_made"
    )
    referee = models.OneToOneField(
        ReferralProfile, on_delete=models.CASCADE, related_name="referred_by"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    qualified_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.referrer.referral_code} → {self.referee.referral_code}"


class RewardLedger(models.Model):
    """Immutable ledger entries for credits and VIP days."""

    class Kind(models.TextChoices):
        CREDIT = "credit", "Credits"
        VIP_DAYS = "vip_days", "VIP Days"

    profile = models.ForeignKey(
        ReferralProfile, on_delete=models.CASCADE, related_name="ledger"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=120)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.profile.referral_code} +{self.amount} {self.kind}"
