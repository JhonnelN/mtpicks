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

    device_id = models.CharField("ID de dispositivo", max_length=128, unique=True, db_index=True)
    email = models.EmailField("Email", blank=True)
    referral_code = models.CharField(
        "Código de referido", max_length=16, unique=True, db_index=True
    )
    credits = models.PositiveIntegerField("Créditos", default=0)
    vip_days = models.PositiveIntegerField("Días VIP", default=0)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Perfil de referido"
        verbose_name_plural = "Perfiles de referido"

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
        PENDING = "pending", "Pendiente"
        QUALIFIED = "qualified", "Calificado"
        REWARDED = "rewarded", "Recompensado"

    referrer = models.ForeignKey(
        ReferralProfile,
        on_delete=models.CASCADE,
        related_name="referrals_made",
        verbose_name="Referidor",
    )
    referee = models.OneToOneField(
        ReferralProfile,
        on_delete=models.CASCADE,
        related_name="referred_by",
        verbose_name="Referido",
    )
    status = models.CharField(
        "Estado", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    qualified_at = models.DateTimeField("Calificado", null=True, blank=True)
    rewarded_at = models.DateTimeField("Recompensado", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Atribución de referido"
        verbose_name_plural = "Atribuciones de referido"

    def __str__(self) -> str:
        return f"{self.referrer.referral_code} → {self.referee.referral_code}"


class RewardLedger(models.Model):
    """Immutable ledger entries for credits and VIP days."""

    class Kind(models.TextChoices):
        CREDIT = "credit", "Créditos"
        VIP_DAYS = "vip_days", "Días VIP"

    profile = models.ForeignKey(
        ReferralProfile,
        on_delete=models.CASCADE,
        related_name="ledger",
        verbose_name="Perfil",
    )
    kind = models.CharField("Tipo", max_length=20, choices=Kind.choices)
    amount = models.PositiveIntegerField("Cantidad")
    reason = models.CharField("Motivo", max_length=120)
    meta = models.JSONField("Meta", default=dict, blank=True)
    created_at = models.DateTimeField("Creado", default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Movimiento de recompensa"
        verbose_name_plural = "Ledger de recompensas"

    def __str__(self) -> str:
        return f"{self.profile.referral_code} +{self.amount} {self.kind}"
