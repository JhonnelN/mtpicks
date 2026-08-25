from django.contrib import admin

from .models import ReferralAttribution, ReferralProfile, RewardLedger


class RewardLedgerInline(admin.TabularInline):
    model = RewardLedger
    extra = 0
    verbose_name = "Movimiento"
    verbose_name_plural = "Ledger"
    readonly_fields = ("kind", "amount", "reason", "meta", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReferralProfile)
class ReferralProfileAdmin(admin.ModelAdmin):
    list_display = (
        "referral_code",
        "device_id",
        "email",
        "credits",
        "vip_days",
        "created_at",
    )
    search_fields = ("referral_code", "device_id", "email")
    date_hierarchy = "created_at"
    inlines = [RewardLedgerInline]
    fieldsets = (
        ("Perfil", {"fields": ("device_id", "email", "referral_code")}),
        ("Recompensas", {"fields": ("credits", "vip_days")}),
        (
            "Auditoría",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(ReferralAttribution)
class ReferralAttributionAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referee", "status", "qualified_at", "rewarded_at")
    list_filter = ("status",)
    search_fields = (
        "referrer__referral_code",
        "referee__referral_code",
        "referrer__device_id",
    )
    autocomplete_fields = ("referrer", "referee")
    date_hierarchy = "created_at"


@admin.register(RewardLedger)
class RewardLedgerAdmin(admin.ModelAdmin):
    list_display = ("profile", "kind", "amount", "reason", "created_at")
    list_filter = ("kind", "reason")
    search_fields = ("profile__referral_code", "reason")
    autocomplete_fields = ("profile",)
    date_hierarchy = "created_at"
    readonly_fields = ("profile", "kind", "amount", "reason", "meta", "created_at")

    def has_add_permission(self, request):
        return False
