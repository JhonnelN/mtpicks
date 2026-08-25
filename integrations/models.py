"""Outbound webhook endpoints and delivery audit log."""

from django.db import models


class EventType(models.TextChoices):
    RACE_NEXT = "race.next", "Carrera siguiente"
    RACE_OFFICIAL = "race.official", "Carrera oficial"
    PICKS_MORNING = "picks.morning_published", "Picks de mañana publicados"
    PICKS_MTP5 = "picks.mtp5_published", "Picks 5 MTP publicados"
    ODDS_MOVED = "odds.moved", "Cuotas movidas"
    REPLAY_READY = "replay.ready", "Replay listo"


class WebhookEndpoint(models.Model):
    """Partner callback URL subscribed to one or more event types."""

    name = models.CharField("Nombre", max_length=120)
    url = models.URLField("URL")
    secret = models.CharField(
        "Secreto",
        max_length=128,
        help_text="Secreto HMAC-SHA256 para la cabecera X-Signature",
    )
    events = models.JSONField(
        "Eventos",
        default=list,
        blank=True,
        help_text="Tipos de evento suscritos; vacío = todos",
    )
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Endpoint webhook"
        verbose_name_plural = "Endpoints webhook"

    def __str__(self) -> str:
        return f"{self.name} ({'activo' if self.is_active else 'inactivo'})"

    def subscribes_to(self, event_type: str) -> bool:
        if not self.events:
            return True
        return event_type in self.events


class WebhookDelivery(models.Model):
    """Audit row for each outbound webhook attempt."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        SUCCESS = "success", "Éxito"
        FAILED = "failed", "Fallido"

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
        verbose_name="Endpoint",
    )
    event_type = models.CharField("Tipo de evento", max_length=64, db_index=True)
    payload = models.JSONField("Payload", default=dict)
    status = models.CharField(
        "Estado", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    status_code = models.PositiveSmallIntegerField("Código HTTP", null=True, blank=True)
    response_body = models.TextField("Respuesta", blank=True)
    attempts = models.PositiveSmallIntegerField("Intentos", default=0)
    next_retry_at = models.DateTimeField("Próximo reintento", null=True, blank=True)
    error_message = models.TextField("Error", blank=True)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    delivered_at = models.DateTimeField("Entregado", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Entrega webhook"
        verbose_name_plural = "Entregas webhook"

    def __str__(self) -> str:
        return f"{self.event_type} → {self.endpoint_id} [{self.status}]"
