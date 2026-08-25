import { Link } from "expo-router";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "@/src/api/client";
import { HorseNumbers } from "@/src/components/HorseNumbers";
import { Screen } from "@/src/components/Screen";
import { StatusChip } from "@/src/components/StatusChip";
import { TrackPickerButton } from "@/src/components/TrackPickerButton";
import { useApiQuery } from "@/src/hooks/useApiQuery";
import { colors, fonts } from "@/src/theme/colors";

export default function VipBoardScreen() {
  const { data, error, loading, refreshing, refresh, reload, trackCode } =
    useApiQuery((base, track) => api.vipBoard(base, track));

  return (
    <Screen
      title="VIP Board"
      subtitle={data ? `${trackCode} · ${data.date}` : trackCode}
      headerRight={<TrackPickerButton code={trackCode} />}
      loading={loading}
      error={error}
      onRetry={reload}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <View style={styles.legend}>
        <Text style={styles.legendText}>Mañana</Text>
        <Text style={styles.legendText}>Última Hora / 5 MTP</Text>
      </View>
      {!data?.races?.length ? (
        <Text style={styles.empty}>Sin carreras en el tablero VIP.</Text>
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
            <Pressable style={styles.row}>
              <Text style={styles.race}>R{race.race_number}</Text>
              <View style={styles.mid}>
                <StatusChip status={race.status} mtp={race.minutes_to_post} />
                <View style={styles.cols}>
                  <HorseNumbers numbers={race.morning} />
                  <HorseNumbers
                    numbers={race.mtp5?.length ? race.mtp5 : race.last_hour}
                    accent="cream"
                  />
                </View>
              </View>
            </Pressable>
          </Link>
        ))
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  legend: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10,
    paddingLeft: 56,
  },
  legendText: {
    fontFamily: fonts.bodySemi,
    color: colors.muted,
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: "uppercase",
    flex: 1,
  },
  empty: { fontFamily: fonts.body, color: colors.muted, fontSize: 15 },
  row: {
    flexDirection: "row",
    gap: 12,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  race: {
    width: 44,
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.gold,
  },
  mid: { flex: 1, gap: 8 },
  cols: { flexDirection: "row", gap: 12 },
});
