import { Link } from "expo-router";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "@/src/api/client";
import { Screen } from "@/src/components/Screen";
import { StatusChip } from "@/src/components/StatusChip";
import { TrackPickerButton } from "@/src/components/TrackPickerButton";
import { useApiQuery } from "@/src/hooks/useApiQuery";
import { colors, fonts } from "@/src/theme/colors";

export default function TodayScreen() {
  const { data, error, loading, refreshing, refresh, reload, trackCode } =
    useApiQuery((base, track) => api.scheduleToday(base, track));

  const races = data?.meets?.flatMap((m) => m.races) ?? [];

  return (
    <Screen
      title="VIP Picker"
      subtitle={
        data
          ? `${trackCode} · ${data.date}`
          : "American Horse Racing"
      }
      headerRight={<TrackPickerButton code={trackCode} />}
      loading={loading}
      error={error}
      onRetry={reload}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <Text style={styles.brandLine}>Carreras de hoy</Text>
      {!races.length ? (
        <Text style={styles.empty}>
          No hay card para {trackCode} hoy. Cambia de pista o carga datos en el
          backend (`seed_demo`).
        </Text>
      ) : (
        races.map((race) => (
          <Link
            key={race.id}
            href={{ pathname: "/race/[id]", params: { id: String(race.id) } }}
            asChild
          >
            <Pressable style={styles.row}>
              <View style={styles.numBlock}>
                <Text style={styles.raceNum}>R{race.race_number}</Text>
              </View>
              <View style={{ flex: 1, gap: 4 }}>
                <Text style={styles.distance}>
                  {race.distance || "—"} · {race.surface_label || race.surface}
                </Text>
                <StatusChip status={race.status} mtp={race.minutes_to_post} />
              </View>
              <Text style={styles.chev}>›</Text>
            </Pressable>
          </Link>
        ))
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  brandLine: {
    fontFamily: fonts.bodySemi,
    color: colors.goldSoft,
    fontSize: 13,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 14,
  },
  empty: {
    fontFamily: fonts.body,
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  numBlock: {
    width: 48,
    alignItems: "center",
  },
  raceNum: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.gold,
  },
  distance: {
    fontFamily: fonts.bodySemi,
    color: colors.cream,
    fontSize: 16,
  },
  chev: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.muted,
  },
});
