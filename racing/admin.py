from django.contrib import admin

from .models import (
    Finisher,
    OddsMovement,
    OddsSnapshot,
    Payout,
    Race,
    RaceDay,
    RaceResult,
    RaceTipSheet,
    Runner,
    ScrapeJob,
    Track,
    VipPick,
)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "state", "timezone", "is_active")
    search_fields = ("code", "name")
    list_filter = ("country", "is_active")


class RaceInline(admin.TabularInline):
    model = Race
    extra = 0
    fields = ("race_number", "distance", "surface", "post_time", "status")


@admin.register(RaceDay)
class RaceDayAdmin(admin.ModelAdmin):
    list_display = ("track", "race_date", "first_post_time", "source", "scraped_at")
    list_filter = ("track__code", "race_date")
    inlines = [RaceInline]


class RunnerInline(admin.TabularInline):
    model = Runner
    extra = 0


class PayoutInline(admin.TabularInline):
    model = Payout
    extra = 0


class VipPickInline(admin.TabularInline):
    model = VipPick
    extra = 0


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "track_code",
        "race_number",
        "race_day",
        "distance",
        "surface",
        "post_time",
        "status",
    )
    list_filter = ("status", "surface", "race_day__track__code")
    search_fields = ("race_name", "race_day__track__code")
    inlines = [RunnerInline, PayoutInline, VipPickInline]


class FinisherInline(admin.TabularInline):
    model = Finisher
    extra = 0


@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ("race", "winning_time", "official_at", "source")
    inlines = [FinisherInline]


@admin.register(RaceTipSheet)
class RaceTipSheetAdmin(admin.ModelAdmin):
    list_display = ("race", "selections", "max_speed", "first_class", "max_pace", "source")
    search_fields = ("race__race_day__track__code",)


@admin.register(OddsSnapshot)
class OddsSnapshotAdmin(admin.ModelAdmin):
    list_display = ("race", "program_number", "odds", "mtp_minutes", "source", "captured_at")
    list_filter = ("mtp_minutes", "source")


@admin.register(OddsMovement)
class OddsMovementAdmin(admin.ModelAdmin):
    list_display = (
        "race",
        "program_number",
        "morning_odds",
        "mtp5_odds",
        "direction",
        "delta",
    )
    list_filter = ("direction",)


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_type",
        "status",
        "source",
        "target_date",
        "races_upserted",
        "started_at",
        "finished_at",
    )
    list_filter = ("job_type", "status", "source")
