from django.urls import path

from .views import ReferralClaimView, ReferralMeView

urlpatterns = [
    path("me/", ReferralMeView.as_view(), name="referral-me"),
    path("claim/", ReferralClaimView.as_view(), name="referral-claim"),
]
