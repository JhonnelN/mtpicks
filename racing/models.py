"""
Domain models for US thoroughbred racing data consumed by the VIP Picker app.
"""

from django.db import models
from django.utils import timezone


class Track(models.Model):
    """US/Canada thoroughbred racetrack."""

    code = models.CharField(max_length=8, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    state = models.CharField(max_length=40, blank=True)
    country = models.CharField(max_length=3, default="USA")
    timezone = models.CharField(max_length=64, default="America/New_York")
    is_active = models.BooleanField(default=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class RaceDay(models.Model):
    """A race card / meet day at a track."""

    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="race_days")
    race_date = models.DateField(db_index=True)
    first_post_time = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=40, default="equibase")
    scraped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("track", "race_date")
        ordering = ["-race_date", "track__code"]
        verbose_name_plural = "race days"

    def __str__(self) -> str:
        return f"{self.track.code} {self.race_date}"


class Race(models.Model):
    """Single race on a race day."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        NEXT = "next", "Next"
        RUNNING = "running", "Running"
        OFFICIAL = "official", "Official"
        CANCELLED = "cancelled", "Cancelled"
        SCRATCHED = "scratched", "Scratched"

    class Surface(models.TextChoices):
        DIRT = "D", "Dirt"
        TURF = "T", "Turf"
        SYNTHETIC = "S", "Synthetic"
        UNKNOWN = "U", "Unknown"

    race_day = models.ForeignKey(RaceDay, on_delete=models.CASCADE, related_name="races")
    race_number = models.PositiveSmallIntegerField()
    race_name = models.CharField(max_length=255, blank=True)
    race_type = models.CharField(max_length=80, blank=True)
    distance = models.CharField(max_length=40, blank=True, help_text="e.g. 1 1/16M")
    distance_furlongs = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    surface = models.CharField(
        max_length=1, choices=Surface.choices, default=Surface.UNKNOWN
    )
    purse = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    post_time = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True
    )
    conditions = models.TextField(blank=True)
    video_replay_url = models.URLField(blank=True)
    external_id = models.CharField(max_length=120, blank=True, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("race_day", "race_number")
        ordering = ["race_day__race_date", "race_number"]

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

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="runners")
    program_number = models.CharField(max_length=8)
    horse_name = models.CharField(max_length=120)
    jockey = models.CharField(max_length=120, blank=True)
    trainer = models.CharField(max_length=120, blank=True)
    morning_line_odds = models.CharField(max_length=20, blank=True)
    weight = models.PositiveSmallIntegerField(null=True, blank=True)
    scratched = models.BooleanField(default=False)
    post_position = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("race", "program_number")
        ordering = ["post_position", "program_number"]

    def __str__(self) -> str:
        return f"#{self.program_number} {self.horse_name}"


class RaceResult(models.Model):
    """Official finish order for a race."""

    race = models.OneToOneField(Race, on_delete=models.CASCADE, related_name="result")
    winning_time = models.CharField(max_length=32, blank=True)
    official_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=40, default="equibase")
    scraped_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Result {self.race}"


class Finisher(models.Model):
    """A finishing position in a race result."""

    result = models.ForeignKey(
        RaceResult, on_delete=models.CASCADE, related_name="finishers"
    )
    position = models.PositiveSmallIntegerField()
    program_number = models.CharField(max_length=8)
    horse_name = models.CharField(max_length=120, blank=True)
    jockey = models.CharField(max_length=120, blank=True)
    trainer = models.CharField(max_length=120, blank=True)
    win_payoff = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    place_payoff = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    show_payoff = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        unique_together = ("result", "position")
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.position}. #{self.program_number}"


class Payout(models.Model):
    """Mutuel payouts (WPS + exotics) for a race."""

    class BetType(models.TextChoices):
        WIN = "W", "Win / Ganador"
        PLACE = "P", "Place / Place"
        SHOW = "S", "Show / Show"
        EXACTA = "EXA", "Exacta"
        TRIFECTA = "TRI", "Trifecta"
        SUPERFECTA = "SUPER", "Superfecta"
        DAILY_DOUBLE = "DD", "Daily Double"
        PICK3 = "P3", "Pick 3"
        PICK4 = "P4", "Pick 4"
        PICK5 = "P5", "Pick 5"
        PICK6 = "P6", "Pick 6"

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="payouts")
    bet_type = models.CharField(max_length=10, choices=BetType.choices)
    combination = models.CharField(
        max_length=64, blank=True, help_text="e.g. 9-2 or 9-2-7"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    base_wager = models.DecimalField(max_digits=8, decimal_places=2, default=2.00)

    class Meta:
        unique_together = ("race", "bet_type", "combination")
        ordering = ["bet_type"]

    def __str__(self) -> str:
        return f"{self.bet_type} {self.combination} ${self.amount}"


class VipPick(models.Model):
    """VIP selection board (morning Our Picks vs 5 MTP update)."""

    class PickWindow(models.TextChoices):
        MORNING = "morning", "Mañana / Our Picks"
        MTP5 = "mtp5", "5 MTP"
        # Kept for API compatibility with older clients
        LAST_HOUR = "last_hour", "Última Hora"

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="vip_picks")
    pick_window = models.CharField(max_length=20, choices=PickWindow.choices)
    # Ordered program numbers, e.g. ["4", "2", "9", "7"]
    selections = models.JSONField(default=list)
    published_at = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("race", "pick_window")
        ordering = ["pick_window"]

    def __str__(self) -> str:
        return f"{self.race} {self.pick_window}: {self.selections}"


class RaceTipSheet(models.Model):
    """
    BetAmerica / brisPICKS-style tip categories (CONSEJOS).

    Each field is an ordered list of program numbers (top 3 typically).
    Our Picks (morning) = first horse of each category.
    """

    race = models.OneToOneField(Race, on_delete=models.CASCADE, related_name="tip_sheet")
    # SELECCIONES
    selections = models.JSONField(default=list, blank=True)
    # VELOCIDAD MÁXIMA
    max_speed = models.JSONField(default=list, blank=True)
    # PRIMERA CLASE
    first_class = models.JSONField(default=list, blank=True)
    # RITMO MÁXIMO
    max_pace = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=40, default="demo")
    published_at = models.DateTimeField(default=timezone.now)

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
        return f"Tips {self.race}"


class OddsSnapshot(models.Model):
    """Odds capture at a given minutes-to-post (null = morning line / open)."""

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="odds_snapshots")
    program_number = models.CharField(max_length=8)
    odds = models.CharField(max_length=20)
    odds_decimal = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    mtp_minutes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Null = morning/open line; 5 = five minutes to post",
    )
    source = models.CharField(max_length=40, default="demo")
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["race", "mtp_minutes"]),
        ]
        ordering = ["program_number", "mtp_minutes"]

    def __str__(self) -> str:
        mtp = "ML" if self.mtp_minutes is None else f"{self.mtp_minutes}MTP"
        return f"{self.race} #{self.program_number} {mtp}={self.odds}"


class OddsMovement(models.Model):
    """Materialized morning → 5 MTP movement for a VIP selection."""

    class Direction(models.TextChoices):
        SHORTENED = "shortened", "Shortened"
        DRIFTED = "drifted", "Drifted"
        UNCHANGED = "unchanged", "Unchanged"

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="odds_movements")
    program_number = models.CharField(max_length=8)
    morning_odds = models.CharField(max_length=20, blank=True)
    mtp5_odds = models.CharField(max_length=20, blank=True)
    morning_decimal = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    mtp5_decimal = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    delta = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="mtp5_decimal - morning_decimal (negative = shortened)",
    )
    direction = models.CharField(
        max_length=20, choices=Direction.choices, default=Direction.UNCHANGED
    )
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("race", "program_number")
        ordering = ["program_number"]

    def __str__(self) -> str:
        return f"{self.race} #{self.program_number} {self.direction}"


class ScrapeJob(models.Model):
    """Audit log for scraper runs."""

    class JobType(models.TextChoices):
        ENTRIES = "entries", "Entries"
        RESULTS = "results", "Results"
        LIVE = "live", "Live"
        NEAR_POST = "near_post", "Near Post"
        TRACKS = "tracks", "Tracks"

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    job_type = models.CharField(max_length=20, choices=JobType.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RUNNING
    )
    source = models.CharField(max_length=40)
    target_date = models.DateField(null=True, blank=True)
    track_codes = models.JSONField(default=list, blank=True)
    races_upserted = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.job_type} {self.status} @ {self.started_at:%Y-%m-%d %H:%M}"
