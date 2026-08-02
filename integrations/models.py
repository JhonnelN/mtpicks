"""Outbound webhook endpoints and delivery audit log."""

from django.db import models


class EventType(models.TextChoices):
    RACE_NEXT = "race.next", "Race Next"
    RACE_OFFICIAL = "race.official", "Race Official"
    PICKS_MORNING = "picks.morning_published", "Morning Picks Published"
    PICKS_MTP5 = "picks.mtp5_published", "5 MTP Picks Published"
    ODDS_MOVED = "odds.moved", "Odds Moved"
    REPLAY_READY = "replay.ready", "Replay Ready"


class WebhookEndpoint(models.Model):
    """Partner callback URL subscribed to one or more event types."""

    name = models.CharField(max_length=120)
    url = models.URLField()
    secret = models.CharField(
        max_length=128,
        help_text="HMAC-SHA256 secret used for X-Signature header",
    )
    events = models.JSONField(
        default=list,
        blank=True,
        help_text="Subscribed event types; empty means all events",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({'active' if self.is_active else 'off'})"

    def subscribes_to(self, event_type: str) -> bool:
        if not self.events:
            return True
        return event_type in self.events


class WebhookDelivery(models.Model):
    """Audit row for each outbound webhook attempt."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    endpoint = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries"
    )
    event_type = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "webhook deliveries"

    def __str__(self) -> str:
        return f"{self.event_type} → {self.endpoint_id} [{self.status}]"
