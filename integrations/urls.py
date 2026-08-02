from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WebhookDeliveryViewSet, WebhookEndpointViewSet, event_catalog, test_emit

router = DefaultRouter()
router.register(r"webhooks", WebhookEndpointViewSet, basename="webhook-endpoint")
router.register(r"deliveries", WebhookDeliveryViewSet, basename="webhook-delivery")

urlpatterns = [
    path("events/", event_catalog, name="integration-events"),
    path("test-emit/", test_emit, name="integration-test-emit"),
    path("", include(router.urls)),
]
