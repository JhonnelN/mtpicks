import { Link } from "expo-router";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "@/src/api/client";
import type { RaceTips } from "@/src/api/types";
import { HorseNumbers } from "@/src/components/HorseNumbers";
import { Screen } from "@/src/components/Screen";
import { StatusChip } from "@/src/components/StatusChip";
import { TrackPickerButton } from "@/src/components/TrackPickerButton";
import { useApiQuery } from "@/src/hooks/useApiQuery";
import { colors, fonts } from "@/src/theme/colors";

function TipsBlock({ tips }: { tips?: RaceTips | null }) {
  if (!tips) return null;
  const entries = [
    tips.selections,
    tips.max_speed,
    tips.first_class,
    tips.max_pace,
  ].filter(Boolean);
  if (!entries.length) return null;
  return (
    <View style={styles.tipsWrap}>
      {entries.map((block) =>
        block ? (
          <View key={block.label} style={styles.tipRow}>
            <Text style={styles.tipLabel}>{block.label}</Text>
            <HorseNumbers numbers={block.horses} accent="success" />
          </View>
        ) : null
      )}
    </View>
  );
}

export default function PicksScreen() {
  const { data, error, loading, refreshing, refresh, reload, trackCode } =
    useApiQuery((base, track) => api.ourPicks(base, track));

  return (
    <Screen
      title="Our Picks"
      subtitle={data ? `${trackCode} · ${data.date}` : trackCode}
      headerRight={<TrackPickerButton code={trackCode} />}
      loading={loading}
      error={error}
      onRetry={reload}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      {!data?.races?.length ? (
        <Text style={styles.empty}>
          Sin picks publicados para esta pista. Crea tip sheets o picks VIP en
          el admin.
        </Text>
      ) : (
        data.races.map((race) => (
          <Link
            key={race.race_id}
            href={{
              pathname: "/race/[id]",
              params: { id: String(race.race_id) },
            }}
            asChild
          >
            <Pressable style={styles.block}>
              <View style={styles.head}>
                <Text style={styles.race}>R{race.race_number}</Text>
                <StatusChip status={race.status} mtp={race.minutes_to_post} />
              </View>
              <TipsBlock tips={race.tips} />
              <View style={styles.cols}>
                <View style={styles.col}>
                  <Text style={styles.colTitle}>Mañana</Text>
                  <HorseNumbers numbers={race.morning} />
                </View>
                <View style={styles.col}>
                  <Text style={styles.colTitle}>5 MTP</Text>
                  <HorseNumbers numbers={race.mtp5} accent="cream" />
                </View>
              </View>
              {!!race.favorites?.length && (
                <View style={styles.favWrap}>
                  <Text style={styles.colTitle}>Favoritos</Text>
                  {race.favorites.slice(0, 4).map((f) => (
                    <Text key={f.program_number} style={styles.fav}>
                      #{f.program_number} · {f.odds}
                    </Text>
                  ))}
                </View>
              )}
              {!!race.odds_movement?.length && (
                <View style={styles.moveWrap}>
                  <Text style={styles.colTitle}>Movimiento</Text>
                  {race.odds_movement.slice(0, 4).map((m) => (
                    <Text key={m.program_number} style={styles.move}>
                      #{m.program_number} {m.morning_odds || "—"} →{" "}
                      {m.mtp5_odds || "—"} ({m.direction})
                    </Text>
                  ))}
                </View>
              )}
            </Pressable>
          </Link>
        ))
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  empty: { fontFamily: fonts.body, color: colors.muted, fontSize: 15 },
  block: {
    borderTopWidth: 1,
    borderTopColor: colors.line,
    paddingVertical: 16,
    gap: 10,
  },
  head: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  race: {
    fontFamily: fonts.display,
    fontSize: 30,
    color: colors.gold,
  },
  tipsWrap: { gap: 8, marginTop: 4 },
  tipRow: { gap: 4 },
  tipLabel: {
    fontFamily: fonts.bodySemi,
    color: colors.success,
    fontSize: 12,
    letterSpacing: 0.8,
  },
  cols: { flexDirection: "row", gap: 16 },
  col: { flex: 1, gap: 6 },
  colTitle: {
    fontFamily: fonts.bodySemi,
    color: colors.muted,
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  favWrap: { gap: 2 },
  fav: { fontFamily: fonts.body, color: colors.cream, fontSize: 14 },
  moveWrap: { gap: 2 },
  move: { fontFamily: fonts.body, color: colors.muted, fontSize: 13 },
});
