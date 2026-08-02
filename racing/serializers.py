"""DRF serializers exposing racing data as JSON for the mobile app."""

from rest_framework import serializers

from .models import (
    Finisher,
    OddsMovement,
    OddsSnapshot,
    Payout,
    Race,
    RaceDay,
    RaceResult,
    Runner,
    Track,
    VipPick,
)


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = [
            "id",
            "code",
            "name",
            "state",
            "country",
            "timezone",
            "is_active",
            "website",
        ]


class RunnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Runner
        fields = [
            "program_number",
            "horse_name",
            "jockey",
            "trainer",
            "morning_line_odds",
            "weight",
            "scratched",
            "post_position",
        ]


class FinisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finisher
        fields = [
            "position",
            "program_number",
            "horse_name",
            "jockey",
            "trainer",
            "win_payoff",
            "place_payoff",
            "show_payoff",
        ]


class PayoutSerializer(serializers.ModelSerializer):
    bet_type_label = serializers.CharField(source="get_bet_type_display", read_only=True)

    class Meta:
        model = Payout
        fields = [
            "bet_type",
            "bet_type_label",
            "combination",
            "amount",
            "base_wager",
        ]


class VipPickSerializer(serializers.ModelSerializer):
    pick_window_label = serializers.CharField(
        source="get_pick_window_display", read_only=True
    )

    class Meta:
        model = VipPick
        fields = [
            "pick_window",
            "pick_window_label",
            "selections",
            "published_at",
            "notes",
        ]


class RaceResultSerializer(serializers.ModelSerializer):
    finishers = FinisherSerializer(many=True, read_only=True)

    class Meta:
        model = RaceResult
        fields = ["winning_time", "official_at", "source", "finishers"]


class RaceListSerializer(serializers.ModelSerializer):
    track_code = serializers.CharField(read_only=True)
    track_name = serializers.CharField(source="race_day.track.name", read_only=True)
    race_date = serializers.DateField(source="race_day.race_date", read_only=True)
    surface_label = serializers.CharField(source="get_surface_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    minutes_to_post = serializers.IntegerField(read_only=True)
    top_three = serializers.SerializerMethodField()
    dividends = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = [
            "id",
            "track_code",
            "track_name",
            "race_date",
            "race_number",
            "race_name",
            "race_type",
            "distance",
            "distance_furlongs",
            "surface",
            "surface_label",
            "purse",
            "post_time",
            "status",
            "status_label",
            "minutes_to_post",
            "video_replay_url",
            "top_three",
            "dividends",
        ]

    def get_top_three(self, obj: Race) -> list[dict]:
        result = getattr(obj, "result", None)
        if not result:
            return []
        return [
            {
                "position": f.position,
                "program_number": f.program_number,
                "horse_name": f.horse_name,
            }
            for f in result.finishers.all()[:3]
        ]

    def get_dividends(self, obj: Race) -> dict:
        """Compact dividend map used by the app (G/P/S/EXA/TRI)."""
        payouts = list(obj.payouts.all())
        mapping = {}
        for payout in payouts:
            key = payout.bet_type
            mapping[key] = {
                "amount": float(payout.amount),
                "combination": payout.combination,
                "base_wager": float(payout.base_wager),
            }
        return mapping


class RaceDetailSerializer(RaceListSerializer):
    runners = RunnerSerializer(many=True, read_only=True)
    result = RaceResultSerializer(read_only=True)
    payouts = PayoutSerializer(many=True, read_only=True)
    vip_picks = VipPickSerializer(many=True, read_only=True)
    conditions = serializers.CharField(read_only=True)

    class Meta(RaceListSerializer.Meta):
        fields = RaceListSerializer.Meta.fields + [
            "conditions",
            "runners",
            "result",
            "payouts",
            "vip_picks",
        ]


class RaceDaySerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    races = RaceListSerializer(many=True, read_only=True)

    class Meta:
        model = RaceDay
        fields = [
            "id",
            "track",
            "race_date",
            "first_post_time",
            "source",
            "scraped_at",
            "races",
        ]


class OddsMovementSerializer(serializers.ModelSerializer):
    direction_label = serializers.CharField(
        source="get_direction_display", read_only=True
    )

    class Meta:
        model = OddsMovement
        fields = [
            "program_number",
            "morning_odds",
            "mtp5_odds",
            "morning_decimal",
            "mtp5_decimal",
            "delta",
            "direction",
            "direction_label",
            "computed_at",
        ]


class OddsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = OddsSnapshot
        fields = [
            "program_number",
            "odds",
            "odds_decimal",
            "mtp_minutes",
            "source",
            "captured_at",
        ]


class TipCategorySerializer(serializers.Serializer):
    label = serializers.CharField()
    horses = serializers.ListField(child=serializers.CharField())
    top = serializers.CharField(allow_null=True)


class RaceTipsSerializer(serializers.Serializer):
    selections = TipCategorySerializer()
    max_speed = TipCategorySerializer()
    first_class = TipCategorySerializer()
    max_pace = TipCategorySerializer()


class FavoriteBoardSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    program_number = serializers.CharField()
    odds = serializers.CharField()
    odds_decimal = serializers.CharField()
    source = serializers.CharField(required=False)


class VipBoardSerializer(serializers.Serializer):
    """Shape matching the VIP Picks comparison table in the app mockup."""

    race_id = serializers.IntegerField()
    track_code = serializers.CharField()
    race_number = serializers.IntegerField()
    race_date = serializers.DateField()
    status = serializers.CharField()
    minutes_to_post = serializers.IntegerField(allow_null=True)
    tips = RaceTipsSerializer(required=False)
    morning = serializers.ListField(child=serializers.CharField(), required=False)
    mtp5 = serializers.ListField(child=serializers.CharField(), required=False)
    # Compat alias for older clients (same as mtp5)
    last_hour = serializers.ListField(child=serializers.CharField(), required=False)
    favorites = FavoriteBoardSerializer(many=True, required=False)
    odds_movement = OddsMovementSerializer(many=True, required=False)


class OurPicksRaceSerializer(serializers.Serializer):
    race_id = serializers.IntegerField()
    track_code = serializers.CharField()
    race_number = serializers.IntegerField()
    race_date = serializers.DateField()
    status = serializers.CharField()
    minutes_to_post = serializers.IntegerField(allow_null=True)
    # BetAmerica CONSEJOS (green boxes)
    tips = RaceTipsSerializer(required=False)
    # First horse of each tip category
    morning = serializers.ListField(child=serializers.CharField())
    mtp5 = serializers.ListField(child=serializers.CharField())
    # BetAmerica pizarra favorites (red circle / Odds column)
    favorites = FavoriteBoardSerializer(many=True, required=False)
    odds_movement = OddsMovementSerializer(many=True)
    snapshots = OddsSnapshotSerializer(many=True, required=False)
