from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    OurPicksView,
    RaceDayViewSet,
    RaceViewSet,
    ResultsFeedView,
    ScheduleTodayView,
    TrackViewSet,
    VipBoardView,
    health,
)

router = DefaultRouter()
router.register(r"tracks", TrackViewSet, basename="track")
router.register(r"race-days", RaceDayViewSet, basename="race-day")
router.register(r"races", RaceViewSet, basename="race")

urlpatterns = [
    path("health/", health, name="health"),
    path("schedule/today/", ScheduleTodayView.as_view(), name="schedule-today"),
    path("vip-board/", VipBoardView.as_view(), name="vip-board"),
    path("our-picks/", OurPicksView.as_view(), name="our-picks"),
    path("results/", ResultsFeedView.as_view(), name="results-feed"),
    path("", include(router.urls)),
]
