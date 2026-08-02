"""Admin token gate for webhook management endpoints."""

from django.conf import settings
from rest_framework.permissions import BasePermission


class IntegrationsAdminPermission(BasePermission):
    """Require header X-Admin-Token matching INTEGRATIONS_ADMIN_TOKEN for writes."""

    def has_permission(self, request, view) -> bool:
        # Reads are public (list endpoints / deliveries for mobile ops dashboards)
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        expected = getattr(settings, "INTEGRATIONS_ADMIN_TOKEN", "") or ""
        if not expected:
            return False
        provided = request.headers.get("X-Admin-Token", "")
        return hmac_compare(provided, expected)


def hmac_compare(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
