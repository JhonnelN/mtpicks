from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .dispatcher import emit
from .models import EventType, WebhookDelivery, WebhookEndpoint
from .permissions import IntegrationsAdminPermission
from .serializers import WebhookDeliverySerializer, WebhookEndpointSerializer


class WebhookEndpointViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = WebhookEndpoint.objects.all()
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IntegrationsAdminPermission]


class WebhookDeliveryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = WebhookDelivery.objects.select_related("endpoint").all()
    serializer_class = WebhookDeliverySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["event_type", "status", "endpoint"]


@api_view(["GET"])
@permission_classes([AllowAny])
def event_catalog(request: Request) -> Response:
    return Response(
        {
            "events": [
                {"type": choice.value, "label": choice.label}
                for choice in EventType
            ]
        }
    )


@api_view(["POST"])
@permission_classes([IntegrationsAdminPermission])
def test_emit(request: Request) -> Response:
    """Admin helper to fire a sample event through the dispatcher."""
    event_type = request.data.get("event_type") or EventType.RACE_NEXT
    payload = request.data.get("payload") or {
        "track_code": "GP",
        "race_number": 1,
        "race_date": "2026-08-02",
        "minutes_to_post": 5,
    }
    summary = emit(event_type, payload)
    return Response(summary)
