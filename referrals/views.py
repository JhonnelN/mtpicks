from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import ReferralError, claim_referral, get_or_create_profile, profile_payload


class ReferralMeView(APIView):
    """Get or create a referral profile for a device_id."""

    def get(self, request: Request) -> Response:
        device_id = request.query_params.get("device_id", "").strip()
        if not device_id:
            return Response(
                {"detail": "device_id query param is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = request.query_params.get("email", "")
        profile, _ = get_or_create_profile(device_id, email=email)
        return Response(profile_payload(profile))

    def post(self, request: Request) -> Response:
        device_id = (request.data.get("device_id") or "").strip()
        email = request.data.get("email") or ""
        if not device_id:
            return Response(
                {"detail": "device_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile, created = get_or_create_profile(device_id, email=email)
        return Response(
            profile_payload(profile),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ReferralClaimView(APIView):
    """Claim a referral code for a device (one-time)."""

    def post(self, request: Request) -> Response:
        device_id = (request.data.get("device_id") or "").strip()
        referral_code = (request.data.get("referral_code") or "").strip()
        email = request.data.get("email") or ""
        try:
            result = claim_referral(device_id, referral_code, email=email)
        except ReferralError as exc:
            return Response(
                {"code": exc.code, "detail": exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(result, status=status.HTTP_201_CREATED)
