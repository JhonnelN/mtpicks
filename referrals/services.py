"""Referral claim + reward grant logic."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from .models import ReferralAttribution, ReferralProfile, RewardLedger


class ReferralError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def get_or_create_profile(device_id: str, email: str = "") -> tuple[ReferralProfile, bool]:
    profile, created = ReferralProfile.objects.get_or_create(
        device_id=device_id,
        defaults={"email": email or ""},
    )
    if email and not profile.email:
        profile.email = email
        profile.save(update_fields=["email", "updated_at"])
    return profile, created


def _daily_reward_count(referrer: ReferralProfile) -> int:
    since = timezone.now() - timedelta(days=1)
    return ReferralAttribution.objects.filter(
        referrer=referrer,
        status=ReferralAttribution.Status.REWARDED,
        rewarded_at__gte=since,
    ).count()


@transaction.atomic
def claim_referral(device_id: str, referral_code: str, email: str = "") -> dict:
    """
    Attribute referee device to referrer code and grant default rewards.

    Qualifying event = successful first claim.
    """
    code = (referral_code or "").strip().upper()
    if not device_id:
        raise ReferralError("missing_device", "device_id is required")
    if not code:
        raise ReferralError("missing_code", "referral_code is required")

    try:
        referrer = ReferralProfile.objects.select_for_update().get(referral_code=code)
    except ReferralProfile.DoesNotExist as exc:
        raise ReferralError("invalid_code", "Referral code not found") from exc

    referee, _ = get_or_create_profile(device_id, email=email)
    if referee.id == referrer.id:
        raise ReferralError("self_referral", "Cannot use your own referral code")

    if hasattr(referee, "referred_by"):
        raise ReferralError("already_claimed", "This device already claimed a referral")

    max_per_day = getattr(settings, "REFERRAL_MAX_REWARDS_PER_DAY", 20)
    if _daily_reward_count(referrer) >= max_per_day:
        raise ReferralError("daily_cap", "Referrer reached daily reward cap")

    attribution = ReferralAttribution.objects.create(
        referrer=referrer,
        referee=referee,
        status=ReferralAttribution.Status.QUALIFIED,
        qualified_at=timezone.now(),
    )

    referrer_credits = getattr(settings, "REFERRAL_REWARD_REFERRER_CREDITS", 10)
    referrer_vip = getattr(settings, "REFERRAL_REWARD_REFERRER_VIP_DAYS", 1)
    referee_credits = getattr(settings, "REFERRAL_REWARD_REFEREE_CREDITS", 5)

    _grant(referrer, RewardLedger.Kind.CREDIT, referrer_credits, "referral_reward", {"referee": referee.id})
    _grant(referrer, RewardLedger.Kind.VIP_DAYS, referrer_vip, "referral_reward", {"referee": referee.id})
    _grant(referee, RewardLedger.Kind.CREDIT, referee_credits, "referral_welcome", {"referrer": referrer.id})

    attribution.status = ReferralAttribution.Status.REWARDED
    attribution.rewarded_at = timezone.now()
    attribution.save(update_fields=["status", "rewarded_at"])

    referrer.refresh_from_db()
    referee.refresh_from_db()
    return {
        "attribution_id": attribution.id,
        "referrer": profile_payload(referrer),
        "referee": profile_payload(referee),
        "rewards": {
            "referrer_credits": referrer_credits,
            "referrer_vip_days": referrer_vip,
            "referee_credits": referee_credits,
        },
    }


def _grant(
    profile: ReferralProfile,
    kind: str,
    amount: int,
    reason: str,
    meta: dict | None = None,
) -> None:
    if amount <= 0:
        return
    RewardLedger.objects.create(
        profile=profile,
        kind=kind,
        amount=amount,
        reason=reason,
        meta=meta or {},
    )
    if kind == RewardLedger.Kind.CREDIT:
        profile.credits += amount
    elif kind == RewardLedger.Kind.VIP_DAYS:
        profile.vip_days += amount
    profile.save(update_fields=["credits", "vip_days", "updated_at"])


def profile_payload(profile: ReferralProfile) -> dict:
    base = getattr(settings, "REFERRAL_SHARE_BASE_URL", "https://vip.example.com/r/{code}")
    share_url = base.replace("{code}", profile.referral_code)
    share_text = (
        f"Usa mi código {profile.referral_code} en American Horse Racing VIP Picker "
        f"y gana créditos VIP: {share_url}"
    )
    stats = (
        ReferralAttribution.objects.filter(referrer=profile)
        .values("status")
        .annotate(count=Count("id"))
    )
    stats_map = {row["status"]: row["count"] for row in stats}
    return {
        "device_id": profile.device_id,
        "email": profile.email,
        "code": profile.referral_code,
        "share_url": share_url,
        "share_text": share_text,
        "credits": profile.credits,
        "vip_days": profile.vip_days,
        "stats": {
            "pending": stats_map.get(ReferralAttribution.Status.PENDING, 0),
            "qualified": stats_map.get(ReferralAttribution.Status.QUALIFIED, 0),
            "rewarded": stats_map.get(ReferralAttribution.Status.REWARDED, 0),
            "total": sum(stats_map.values()),
        },
    }
