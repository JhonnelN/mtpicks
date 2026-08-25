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
    list_editable = ("is_active",)
    fieldsets = (
        ("Identificación", {"fields": ("code", "name", "state", "country")}),
        ("Operación", {"fields": ("timezone", "is_active", "website")}),
        (
            "Auditoría",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


class RaceInline(admin.TabularInline):
    model = Race
    extra = 0
    fields = ("race_number", "distance", "surface", "post_time", "status")
    show_change_link = True
    verbose_name = "Carrera"
    verbose_name_plural = "Carreras"


@admin.register(RaceDay)
class RaceDayAdmin(admin.ModelAdmin):
    list_display = ("track", "race_date", "first_post_time", "source", "scraped_at")
    list_filter = ("track__code", "source")
    search_fields = ("track__code", "track__name")
    date_hierarchy = "race_date"
    autocomplete_fields = ("track",)
    inlines = [RaceInline]
    fieldsets = (
        (None, {"fields": ("track", "race_date", "first_post_time")}),
        ("Origen", {"fields": ("source", "scraped_at")}),
    )


class RunnerInline(admin.TabularInline):
    model = Runner
    extra = 0
    verbose_name = "Participante"
    verbose_name_plural = "Participantes"
    fields = (
        "program_number",
        "horse_name",
        "jockey",
        "trainer",
        "morning_line_odds",
        "scratched",
        "post_position",
    )


class PayoutInline(admin.TabularInline):
    model = Payout
    extra = 0
    verbose_name = "Dividendo"
    verbose_name_plural = "Dividendos"


class VipPickInline(admin.TabularInline):
    model = VipPick
    extra = 0
    verbose_name = "Pick VIP"
    verbose_name_plural = "Picks VIP"
    fields = ("pick_window", "selections", "published_at", "notes")


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
    search_fields = ("race_name", "race_day__track__code", "external_id")
    date_hierarchy = "post_time"
    autocomplete_fields = ("race_day",)
    inlines = [RunnerInline, PayoutInline, VipPickInline]
    fieldsets = (
        (
            "Carrera",
            {
                "fields": (
                    "race_day",
                    "race_number",
                    "race_name",
                    "race_type",
                    "status",
                )
            },
        ),
        (
            "Condiciones",
            {
                "fields": (
                    "distance",
                    "distance_furlongs",
                    "surface",
                    "purse",
                    "conditions",
                )
            },
        ),
        ("Horario y media", {"fields": ("post_time", "video_replay_url")}),
        (
            "Técnico",
            {
                "fields": ("external_id", "raw_payload", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")


class FinisherInline(admin.TabularInline):
    model = Finisher
    extra = 0
    verbose_name = "Llegada"
    verbose_name_plural = "Llegada"
    fields = (
        "position",
        "program_number",
        "horse_name",
        "jockey",
        "win_payoff",
        "place_payoff",
        "show_payoff",
    )


@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ("race", "winning_time", "official_at", "source")
    search_fields = ("race__race_day__track__code",)
    date_hierarchy = "official_at"
    autocomplete_fields = ("race",)
    inlines = [FinisherInline]


@admin.register(RaceTipSheet)
class RaceTipSheetAdmin(admin.ModelAdmin):
    list_display = (
        "race",
        "selections",
        "max_speed",
        "first_class",
        "max_pace",
        "source",
        "published_at",
    )
    search_fields = ("race__race_day__track__code",)
    autocomplete_fields = ("race",)
    date_hierarchy = "published_at"
    fieldsets = (
        ("Carrera", {"fields": ("race", "source", "published_at")}),
        (
            "Consejos (CONSEJOS)",
            {
                "fields": ("selections", "max_speed", "first_class", "max_pace"),
                "description": (
                    "Listas JSON de números de programa. "
                    "Our Picks (mañana) = el primero de cada categoría."
                ),
            },
        ),
    )


@admin.register(VipPick)
class VipPickAdmin(admin.ModelAdmin):
    list_display = ("race", "pick_window", "selections", "published_at")
    list_filter = ("pick_window",)
    search_fields = ("race__race_day__track__code",)
    autocomplete_fields = ("race",)
    date_hierarchy = "published_at"


@admin.register(OddsSnapshot)
class OddsSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "race",
        "program_number",
        "odds",
        "mtp_minutes",
        "source",
        "captured_at",
    )
    list_filter = ("mtp_minutes", "source")
    search_fields = ("race__race_day__track__code", "program_number")
    autocomplete_fields = ("race",)
    date_hierarchy = "captured_at"


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
    search_fields = ("race__race_day__track__code", "program_number")
    autocomplete_fields = ("race",)


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
    search_fields = ("error_message", "source")
    date_hierarchy = "started_at"
    readonly_fields = (
        "job_type",
        "status",
        "source",
        "target_date",
        "track_codes",
        "races_upserted",
        "error_message",
        "started_at",
        "finished_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
