from django.contrib import admin

from .models import ReferralAttribution, ReferralProfile, RewardLedger


class RewardLedgerInline(admin.TabularInline):
    model = RewardLedger
    extra = 0
    readonly_fields = ("kind", "amount", "reason", "meta", "created_at")


@admin.register(ReferralProfile)
class ReferralProfileAdmin(admin.ModelAdmin):
    list_display = ("referral_code", "device_id", "email", "credits", "vip_days", "created_at")
    search_fields = ("referral_code", "device_id", "email")
    inlines = [RewardLedgerInline]


@admin.register(ReferralAttribution)
class ReferralAttributionAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referee", "status", "qualified_at", "rewarded_at")
    list_filter = ("status",)


@admin.register(RewardLedger)
class RewardLedgerAdmin(admin.ModelAdmin):
    list_display = ("profile", "kind", "amount", "reason", "created_at")
    list_filter = ("kind", "reason")
