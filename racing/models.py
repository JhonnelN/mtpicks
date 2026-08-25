"""
Domain models for US thoroughbred racing data consumed by the VIP Picker app.
"""

from django.db import models
from django.utils import timezone


class Track(models.Model):
    """US/Canada thoroughbred racetrack."""

    code = models.CharField("Código", max_length=8, unique=True, db_index=True)
    name = models.CharField("Nombre", max_length=120)
    state = models.CharField("Estado", max_length=40, blank=True)
    country = models.CharField("País", max_length=3, default="USA")
    timezone = models.CharField("Zona horaria", max_length=64, default="America/New_York")
    is_active = models.BooleanField("Activo", default=True)
    website = models.URLField("Sitio web", blank=True)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Hipódromo"
        verbose_name_plural = "Hipódromos"

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class RaceDay(models.Model):
    """A race card / meet day at a track."""

    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name="race_days",
        verbose_name="Hipódromo",
    )
    race_date = models.DateField("Fecha", db_index=True)
    first_post_time = models.DateTimeField("Primer post", null=True, blank=True)
    source = models.CharField("Fuente", max_length=40, default="equibase")
    scraped_at = models.DateTimeField("Scrapeado", null=True, blank=True)

    class Meta:
        unique_together = ("track", "race_date")
        ordering = ["-race_date", "track__code"]
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"

    def __str__(self) -> str:
        return f"{self.track.code} {self.race_date}"


class Race(models.Model):
    """Single race on a race day."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Programada"
        NEXT = "next", "Siguiente"
        RUNNING = "running", "En curso"
        OFFICIAL = "official", "Oficial"
        CANCELLED = "cancelled", "Cancelada"
        SCRATCHED = "scratched", "Anulada"

    class Surface(models.TextChoices):
        DIRT = "D", "Dirt"
        TURF = "T", "Turf"
        SYNTHETIC = "S", "Sintético"
        UNKNOWN = "U", "Desconocido"

    race_day = models.ForeignKey(
        RaceDay,
        on_delete=models.CASCADE,
        related_name="races",
        verbose_name="Jornada",
    )
    race_number = models.PositiveSmallIntegerField("Nº carrera")
    race_name = models.CharField("Nombre", max_length=255, blank=True)
    race_type = models.CharField("Tipo", max_length=80, blank=True)
    distance = models.CharField(
        "Distancia", max_length=40, blank=True, help_text="ej. 1 1/16M"
    )
    distance_furlongs = models.DecimalField(
        "Furlongs", max_digits=6, decimal_places=2, null=True, blank=True
    )
    surface = models.CharField(
        "Pista", max_length=1, choices=Surface.choices, default=Surface.UNKNOWN
    )
    purse = models.DecimalField(
        "Bolsa", max_digits=12, decimal_places=2, null=True, blank=True
    )
    post_time = models.DateTimeField("Hora de post", null=True, blank=True, db_index=True)
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
    )
    conditions = models.TextField("Condiciones", blank=True)
    video_replay_url = models.URLField("Replay", blank=True)
    external_id = models.CharField("ID externo", max_length=120, blank=True, db_index=True)
    raw_payload = models.JSONField("Payload bruto", default=dict, blank=True)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        unique_together = ("race_day", "race_number")
        ordering = ["race_day__race_date", "race_number"]
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"

    def __str__(self) -> str:
        return f"{self.race_day.track.code}-R{self.race_number} ({self.race_day.race_date})"

    @property
    def track_code(self) -> str:
        return self.race_day.track.code

    @property
    def minutes_to_post(self) -> int | None:
        if not self.post_time:
            return None
        delta = self.post_time - timezone.now()
        return int(delta.total_seconds() // 60)


class Runner(models.Model):
    """Horse entered in a race (program number / saddle cloth)."""

    race = models.ForeignKey(
        Race, on_delete=models.CASCADE, related_name="runners", verbose_name="Carrera"
    )
    program_number = models.CharField("Nº programa", max_length=8)
    horse_name = models.CharField("Caballo", max_length=120)
    jockey = models.CharField("Jinete", max_length=120, blank=True)
    trainer = models.CharField("Entrenador", max_length=120, blank=True)
    morning_line_odds = models.CharField("Cuota mañana", max_length=20, blank=True)
    weight = models.PositiveSmallIntegerField("Peso", null=True, blank=True)
    scratched = models.BooleanField("Retirado", default=False)
    post_position = models.PositiveSmallIntegerField(
        "Post", null=True, blank=True
    )

    class Meta:
        unique_together = ("race", "program_number")
        ordering = ["post_position", "program_number"]
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"

    def __str__(self) -> str:
        return f"#{self.program_number} {self.horse_name}"


class RaceResult(models.Model):
    """Official finish order for a race."""

    race = models.OneToOneField(
        Race, on_delete=models.CASCADE, related_name="result", verbose_name="Carrera"
    )
    winning_time = models.CharField("Tiempo ganador", max_length=32, blank=True)
    official_at = models.DateTimeField("Oficializado", null=True, blank=True)
    source = models.CharField("Fuente", max_length=40, default="equibase")
    scraped_at = models.DateTimeField("Scrapeado", auto_now=True)

    class Meta:
        verbose_name = "Resultado"
        verbose_name_plural = "Resultados"

    def __str__(self) -> str:
        return f"Resultado {self.race}"


class Finisher(models.Model):
    """A finishing position in a race result."""

    result = models.ForeignKey(
        RaceResult,
        on_delete=models.CASCADE,
        related_name="finishers",
        verbose_name="Resultado",
    )
    position = models.PositiveSmallIntegerField("Posición")
    program_number = models.CharField("Nº programa", max_length=8)
    horse_name = models.CharField("Caballo", max_length=120, blank=True)
    jockey = models.CharField("Jinete", max_length=120, blank=True)
    trainer = models.CharField("Entrenador", max_length=120, blank=True)
    win_payoff = models.DecimalField(
        "Pago win", max_digits=10, decimal_places=2, null=True, blank=True
    )
    place_payoff = models.DecimalField(
        "Pago place", max_digits=10, decimal_places=2, null=True, blank=True
    )
    show_payoff = models.DecimalField(
        "Pago show", max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        unique_together = ("result", "position")
        ordering = ["position"]
        verbose_name = "Llegada"
        verbose_name_plural = "Llegada"

    def __str__(self) -> str:
        return f"{self.position}. #{self.program_number}"


class Payout(models.Model):
    """Mutuel payouts (WPS + exotics) for a race."""

    class BetType(models.TextChoices):
        WIN = "W", "Win / Ganador"
        PLACE = "P", "Place"
        SHOW = "S", "Show"
        EXACTA = "EXA", "Exacta"
        TRIFECTA = "TRI", "Trifecta"
        SUPERFECTA = "SUPER", "Superfecta"
        DAILY_DOUBLE = "DD", "Daily Double"
        PICK3 = "P3", "Pick 3"
        PICK4 = "P4", "Pick 4"
        PICK5 = "P5", "Pick 5"
        PICK6 = "P6", "Pick 6"

    race = models.ForeignKey(
        Race, on_delete=models.CASCADE, related_name="payouts", verbose_name="Carrera"
    )
    bet_type = models.CharField("Tipo de apuesta", max_length=10, choices=BetType.choices)
    combination = models.CharField(
        "Combinación", max_length=64, blank=True, help_text="ej. 9-2 o 9-2-7"
    )
    amount = models.DecimalField("Importe", max_digits=12, decimal_places=2)
    base_wager = models.DecimalField(
        "Base", max_digits=8, decimal_places=2, default=2.00
    )

    class Meta:
        unique_together = ("race", "bet_type", "combination")
        ordering = ["bet_type"]
        verbose_name = "Dividendo"
        verbose_name_plural = "Dividendos"

    def __str__(self) -> str:
        return f"{self.bet_type} {self.combination} ${self.amount}"


class VipPick(models.Model):
    """VIP selection board (morning Our Picks vs 5 MTP update)."""

    class PickWindow(models.TextChoices):
        MORNING = "morning", "Mañana / Our Picks"
        MTP5 = "mtp5", "5 MTP"
        # Kept for API compatibility with older clients
        LAST_HOUR = "last_hour", "Última Hora"

    race = models.ForeignKey(
        Race, on_delete=models.CASCADE, related_name="vip_picks", verbose_name="Carrera"
    )
    pick_window = models.CharField(
        "Ventana", max_length=20, choices=PickWindow.choices
    )
    # Ordered program numbers, e.g. ["4", "2", "9", "7"]
    selections = models.JSONField("Selecciones", default=list)
    published_at = models.DateTimeField("Publicado", default=timezone.now)
    notes = models.CharField("Notas", max_length=255, blank=True)

    class Meta:
        unique_together = ("race", "pick_window")
        ordering = ["pick_window"]
        verbose_name = "Pick VIP"
        verbose_name_plural = "Picks VIP"

    def __str__(self) -> str:
        return f"{self.race} {self.pick_window}: {self.selections}"


class RaceTipSheet(models.Model):
    """
    BetAmerica / brisPICKS-style tip categories (CONSEJOS).

    Each field is an ordered list of program numbers (top 3 typically).
    Our Picks (morning) = first horse of each category.
    """

    race = models.OneToOneField(
        Race, on_delete=models.CASCADE, related_name="tip_sheet", verbose_name="Carrera"
    )
    # SELECCIONES
    selections = models.JSONField("Selecciones", default=list, blank=True)
    # VELOCIDAD MÁXIMA
    max_speed = models.JSONField("Velocidad máxima", default=list, blank=True)
    # PRIMERA CLASE
    first_class = models.JSONField("Primera clase", default=list, blank=True)
    # RITMO MÁXIMO
    max_pace = models.JSONField("Ritmo máximo", default=list, blank=True)
    source = models.CharField("Fuente", max_length=40, default="demo")
    published_at = models.DateTimeField("Publicado", default=timezone.now)

    class Meta:
        verbose_name = "Hoja de consejos"
        verbose_name_plural = "Hojas de consejos"

    def morning_tops(self) -> list[str]:
        """First horse from each tip category → Mañana / Our Picks."""
        tops: list[str] = []
        for bucket in (self.selections, self.max_speed, self.first_class, self.max_pace):
            if bucket:
                tops.append(str(bucket[0]))
        return tops

    def as_tips_payload(self) -> dict:
        def block(label: str, horses: list) -> dict:
            horses = [str(h) for h in (horses or [])]
            return {
                "label": label,
                "horses": horses,
                "top": horses[0] if horses else None,
            }

        return {
            "selections": block("SELECCIONES", self.selections),
            "max_speed": block("VELOCIDAD MAXIMA", self.max_speed),
            "first_class": block("PRIMERA CLASE", self.first_class),
            "max_pace": block("RITMO MAXIMO", self.max_pace),
        }

    def __str__(self) -> str:
        return f"Consejos {self.race}"


class OddsSnapshot(models.Model):
    """Odds capture at a given minutes-to-post (null = morning line / open)."""

    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name="odds_snapshots",
        verbose_name="Carrera",
    )
    program_number = models.CharField("Nº programa", max_length=8)
    odds = models.CharField("Cuota", max_length=20)
    odds_decimal = models.DecimalField(
        "Cuota decimal", max_digits=10, decimal_places=4, null=True, blank=True
    )
    mtp_minutes = models.PositiveSmallIntegerField(
        "Minutos a post",
        null=True,
        blank=True,
        help_text="Vacío = línea de mañana; 5 = cinco minutos a post",
    )
    source = models.CharField("Fuente", max_length=40, default="demo")
    captured_at = models.DateTimeField("Capturado", default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["race", "mtp_minutes"]),
        ]
        ordering = ["program_number", "mtp_minutes"]
        verbose_name = "Snapshot de cuotas"
        verbose_name_plural = "Snapshots de cuotas"

    def __str__(self) -> str:
        mtp = "ML" if self.mtp_minutes is None else f"{self.mtp_minutes}MTP"
        return f"{self.race} #{self.program_number} {mtp}={self.odds}"


class OddsMovement(models.Model):
    """Materialized morning → 5 MTP movement for a VIP selection."""

    class Direction(models.TextChoices):
        SHORTENED = "shortened", "Acortó"
        DRIFTED = "drifted", "Alargó"
        UNCHANGED = "unchanged", "Sin cambio"

    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name="odds_movements",
        verbose_name="Carrera",
    )
    program_number = models.CharField("Nº programa", max_length=8)
    morning_odds = models.CharField("Cuota mañana", max_length=20, blank=True)
    mtp5_odds = models.CharField("Cuota 5 MTP", max_length=20, blank=True)
    morning_decimal = models.DecimalField(
        "Decimal mañana", max_digits=10, decimal_places=4, null=True, blank=True
    )
    mtp5_decimal = models.DecimalField(
        "Decimal 5 MTP", max_digits=10, decimal_places=4, null=True, blank=True
    )
    delta = models.DecimalField(
        "Delta",
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="mtp5_decimal - morning_decimal (negativo = acortó)",
    )
    direction = models.CharField(
        "Dirección",
        max_length=20,
        choices=Direction.choices,
        default=Direction.UNCHANGED,
    )
    computed_at = models.DateTimeField("Calculado", auto_now=True)

    class Meta:
        unique_together = ("race", "program_number")
        ordering = ["program_number"]
        verbose_name = "Movimiento de cuotas"
        verbose_name_plural = "Movimientos de cuotas"

    def __str__(self) -> str:
        return f"{self.race} #{self.program_number} {self.direction}"


class ScrapeJob(models.Model):
    """Audit log for scraper runs."""

    class JobType(models.TextChoices):
        ENTRIES = "entries", "Entries"
        RESULTS = "results", "Resultados"
        LIVE = "live", "En vivo"
        NEAR_POST = "near_post", "Cerca del post"
        TRACKS = "tracks", "Hipódromos"

    class Status(models.TextChoices):
        RUNNING = "running", "En ejecución"
        SUCCESS = "success", "Éxito"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Fallido"

    job_type = models.CharField("Tipo", max_length=20, choices=JobType.choices)
    status = models.CharField(
        "Estado", max_length=20, choices=Status.choices, default=Status.RUNNING
    )
    source = models.CharField("Fuente", max_length=40)
    target_date = models.DateField("Fecha objetivo", null=True, blank=True)
    track_codes = models.JSONField("Códigos de pista", default=list, blank=True)
    races_upserted = models.PositiveIntegerField("Carreras actualizadas", default=0)
    error_message = models.TextField("Error", blank=True)
    started_at = models.DateTimeField("Inicio", auto_now_add=True)
    finished_at = models.DateTimeField("Fin", null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Job de scrape"
        verbose_name_plural = "Jobs de scrape"

    def __str__(self) -> str:
        return f"{self.job_type} {self.status} @ {self.started_at:%Y-%m-%d %H:%M}"
