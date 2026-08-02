from django.contrib import admin

from .models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "url")


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "endpoint",
        "status",
        "status_code",
        "attempts",
        "created_at",
    )
    list_filter = ("status", "event_type")
    readonly_fields = ("payload", "response_body", "error_message")
