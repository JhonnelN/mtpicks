from rest_framework import serializers

from .models import WebhookDelivery, WebhookEndpoint


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = [
            "id",
            "name",
            "url",
            "secret",
            "events",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"secret": {"write_only": True}}


class WebhookDeliverySerializer(serializers.ModelSerializer):
    endpoint_name = serializers.CharField(source="endpoint.name", read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            "id",
            "endpoint",
            "endpoint_name",
            "event_type",
            "payload",
            "status",
            "status_code",
            "attempts",
            "next_retry_at",
            "error_message",
            "created_at",
            "delivered_at",
        ]
        read_only_fields = fields
