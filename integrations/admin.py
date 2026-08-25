from django.contrib import admin

from .models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "url")
    list_editable = ("is_active",)
    fieldsets = (
        ("Endpoint", {"fields": ("name", "url", "is_active")}),
        (
            "Seguridad y eventos",
            {
                "fields": ("secret", "events"),
                "description": "Lista JSON de eventos; vacía = suscrito a todos.",
            },
        ),
        (
            "Auditoría",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


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
    search_fields = ("event_type", "endpoint__name", "error_message")
    date_hierarchy = "created_at"
    autocomplete_fields = ("endpoint",)
    readonly_fields = (
        "endpoint",
        "event_type",
        "payload",
        "status",
        "status_code",
        "response_body",
        "attempts",
        "next_retry_at",
        "error_message",
        "created_at",
        "delivered_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow opening the detail page; all fields are readonly.
        return True
