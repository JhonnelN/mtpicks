"""Custom AdminSite with Spanish dashboard stats for Jazzmin index."""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils import timezone


class VipPickerAdminSite(AdminSite):
    site_header = "American Horse Racing VIP Picker"
    site_title = "VIP Picker Admin"
    index_title = "Panel de control"
    index_template = "admin/vip_index.html"

    def index(self, request, extra_context=None):
        from integrations.models import WebhookDelivery, WebhookEndpoint
        from racing.models import Race, ScrapeJob
        from referrals.models import ReferralProfile

        today = timezone.localdate()
        recent_jobs = ScrapeJob.objects.order_by("-started_at")[:8]
        failed_jobs = ScrapeJob.objects.filter(status=ScrapeJob.Status.FAILED).count()

        stats = {
            "races_today": Race.objects.filter(race_day__race_date=today).count(),
            "scrape_jobs_total": ScrapeJob.objects.count(),
            "scrape_jobs_failed": failed_jobs,
            "referrals_total": ReferralProfile.objects.count(),
            "webhooks_active": WebhookEndpoint.objects.filter(is_active=True).count(),
            "webhook_deliveries_today": WebhookDelivery.objects.filter(
                created_at__date=today
            ).count(),
            "recent_scrape_jobs": recent_jobs,
            "today": today,
        }
        context = {**(extra_context or {}), "vip_stats": stats}
        return super().index(request, extra_context=context)


# Replace the default site instance used by django.contrib.admin and Jazzmin.
admin.site.__class__ = VipPickerAdminSite
admin.site.site_header = VipPickerAdminSite.site_header
admin.site.site_title = VipPickerAdminSite.site_title
admin.site.index_title = VipPickerAdminSite.index_title
admin.site.index_template = VipPickerAdminSite.index_template
