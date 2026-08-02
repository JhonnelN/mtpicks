"""REST API views for tracks, schedules, results and VIP picks."""

from datetime import date

from django.db.models import Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Race, RaceDay, Track, VipPick
from .odds import favorites_board
from .serializers import (
    OddsMovementSerializer,
    OurPicksRaceSerializer,
    RaceDaySerializer,
    RaceDetailSerializer,
    RaceListSerializer,
    TrackSerializer,
    VipBoardSerializer,
    VipPickSerializer,
)


def _mtp5_selections(picks: dict) -> list:
    """Prefer mtp5 window; fall back to legacy last_hour."""
    return picks.get(VipPick.PickWindow.MTP5) or picks.get(
        VipPick.PickWindow.LAST_HOUR, []
    )


def _tips_and_morning(race: Race) -> tuple[dict | None, list]:
    """Build BetAmerica tip sheet + morning tops (first of each category)."""
    tip_sheet = getattr(race, "tip_sheet", None)
    if tip_sheet is None:
        return None, []
    return tip_sheet.as_tips_payload(), tip_sheet.morning_tops()


class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Track.objects.filter(is_active=True)
    serializer_class = TrackSerializer
    lookup_field = "code"
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["code", "name", "state"]
    ordering_fields = ["name", "code"]


class RaceDayViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RaceDaySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["track__code", "race_date"]
    ordering_fields = ["race_date", "track__code"]

    def get_queryset(self):
        return (
            RaceDay.objects.select_related("track")
            .prefetch_related(
                Prefetch(
                    "races",
                    queryset=Race.objects.select_related("result")
                    .prefetch_related("result__finishers", "payouts")
                    .order_by("race_number"),
                )
            )
            .all()
        )


class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "race_day__track__code": ["exact"],
        "race_day__race_date": ["exact", "gte", "lte"],
        "status": ["exact", "in"],
        "surface": ["exact"],
        "race_number": ["exact"],
    }
    search_fields = ["race_name", "race_type", "race_day__track__code"]
    ordering_fields = ["post_time", "race_number", "race_day__race_date"]
    ordering = ["race_day__race_date", "race_number"]

    def get_queryset(self):
        return Race.objects.select_related(
            "race_day__track", "result", "tip_sheet"
        ).prefetch_related(
            "runners",
            "result__finishers",
            "payouts",
            "vip_picks",
            "odds_movements",
            "odds_snapshots",
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RaceDetailSerializer
        return RaceListSerializer

    @action(detail=True, methods=["get"])
    def picks(self, request: Request, pk=None):
        race = self.get_object()
        picks = race.vip_picks.all()
        return Response(VipPickSerializer(picks, many=True).data)

    @action(detail=True, methods=["get"])
    def results(self, request: Request, pk=None):
        race = self.get_object()
        return Response(RaceDetailSerializer(race).data)

    @action(detail=True, methods=["get"], url_path="odds-movement")
    def odds_movement(self, request: Request, pk=None):
        race = self.get_object()
        return Response(
            {
                "race_id": race.id,
                "track_code": race.track_code,
                "race_number": race.race_number,
                "favorites": favorites_board(race),
                "movements": OddsMovementSerializer(
                    race.odds_movements.all(), many=True
                ).data,
            }
        )


class ScheduleTodayView(APIView):
    """Today's cards across all configured tracks (app home feed)."""

    def get(self, request: Request) -> Response:
        target = request.query_params.get("date")
        race_date = date.fromisoformat(target) if target else timezone.localdate()
        track_code = request.query_params.get("track")

        qs = (
            RaceDay.objects.filter(race_date=race_date)
            .select_related("track")
            .prefetch_related(
                Prefetch(
                    "races",
                    queryset=Race.objects.select_related("result")
                    .prefetch_related("result__finishers", "payouts", "vip_picks")
                    .order_by("race_number"),
                )
            )
        )
        if track_code:
            qs = qs.filter(track__code=track_code.upper())

        payload = {
            "date": race_date.isoformat(),
            "timezone": timezone.get_current_timezone_name(),
            "meets": RaceDaySerializer(qs, many=True).data,
        }
        return Response(payload)


class VipBoardView(APIView):
    """VIP Picks board: tips, morning tops, favorites board, 5 MTP + movement."""

    def get(self, request: Request) -> Response:
        track_code = request.query_params.get("track")
        target = request.query_params.get("date")
        race_date = date.fromisoformat(target) if target else timezone.localdate()

        races = (
            Race.objects.filter(race_day__race_date=race_date)
            .select_related("race_day__track", "tip_sheet")
            .prefetch_related("vip_picks", "odds_movements", "odds_snapshots", "runners")
            .order_by("race_number")
        )
        if track_code:
            races = races.filter(race_day__track__code=track_code.upper())

        boards = []
        for race in races:
            picks = {p.pick_window: p.selections for p in race.vip_picks.all()}
            tips, morning_from_tips = _tips_and_morning(race)
            morning = morning_from_tips or picks.get(VipPick.PickWindow.MORNING, [])
            mtp5 = _mtp5_selections(picks)
            boards.append(
                {
                    "race_id": race.id,
                    "track_code": race.track_code,
                    "race_number": race.race_number,
                    "race_date": race.race_day.race_date,
                    "status": race.status,
                    "minutes_to_post": race.minutes_to_post,
                    "tips": tips,
                    "morning": morning,
                    "mtp5": mtp5,
                    "last_hour": mtp5,
                    "favorites": favorites_board(race),
                    "odds_movement": OddsMovementSerializer(
                        race.odds_movements.all(), many=True
                    ).data,
                }
            )
        return Response(
            {
                "date": race_date.isoformat(),
                "track": track_code.upper() if track_code else None,
                "races": VipBoardSerializer(boards, many=True).data,
            }
        )


class OurPicksView(APIView):
    """
    Our Picks aligned to BetAmerica CONSEJOS + pizarra favorites.

    - tips.* / morning  → green boxes (first horse of each category)
    - favorites         → red odds board (shortest odds first)
    - odds_movement     → morning → 5 MTP deltas for VIP selections
    """

    def get(self, request: Request) -> Response:
        track_code = request.query_params.get("track")
        target = request.query_params.get("date")
        race_date = date.fromisoformat(target) if target else timezone.localdate()

        races = (
            Race.objects.filter(race_day__race_date=race_date)
            .select_related("race_day__track", "tip_sheet")
            .prefetch_related(
                "vip_picks", "odds_movements", "odds_snapshots", "runners"
            )
            .order_by("race_number")
        )
        if track_code:
            races = races.filter(race_day__track__code=track_code.upper())

        items = []
        for race in races:
            picks = {p.pick_window: p.selections for p in race.vip_picks.all()}
            tips, morning_from_tips = _tips_and_morning(race)
            morning = morning_from_tips or picks.get(VipPick.PickWindow.MORNING, [])
            if not morning and not tips:
                continue
            mtp5 = _mtp5_selections(picks)
            items.append(
                {
                    "race_id": race.id,
                    "track_code": race.track_code,
                    "race_number": race.race_number,
                    "race_date": race.race_day.race_date,
                    "status": race.status,
                    "minutes_to_post": race.minutes_to_post,
                    "tips": tips,
                    "morning": morning,
                    "mtp5": mtp5,
                    "favorites": favorites_board(race),
                    "odds_movement": OddsMovementSerializer(
                        race.odds_movements.all(), many=True
                    ).data,
                    "snapshots": [
                        {
                            "program_number": s.program_number,
                            "odds": s.odds,
                            "odds_decimal": s.odds_decimal,
                            "mtp_minutes": s.mtp_minutes,
                            "source": s.source,
                            "captured_at": s.captured_at,
                        }
                        for s in race.odds_snapshots.all()
                    ],
                }
            )
        return Response(
            {
                "date": race_date.isoformat(),
                "track": track_code.upper() if track_code else None,
                "races": OurPicksRaceSerializer(items, many=True).data,
            }
        )


class ResultsFeedView(APIView):
    """Compact results feed with llegada + dividendos for finished races."""

    def get(self, request: Request) -> Response:
        track_code = request.query_params.get("track")
        target = request.query_params.get("date")
        race_date = date.fromisoformat(target) if target else timezone.localdate()

        races = (
            Race.objects.filter(
                race_day__race_date=race_date,
                status=Race.Status.OFFICIAL,
            )
            .select_related("race_day__track", "result")
            .prefetch_related("result__finishers", "payouts")
            .order_by("race_number")
        )
        if track_code:
            races = races.filter(race_day__track__code=track_code.upper())

        return Response(
            {
                "date": race_date.isoformat(),
                "track": track_code.upper() if track_code else None,
                "results": RaceListSerializer(races, many=True).data,
            }
        )


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response(
        {
            "status": "ok",
            "service": "american-horse-racing-vip-picker",
            "time": timezone.now().isoformat(),
        },
        status=status.HTTP_200_OK,
    )
