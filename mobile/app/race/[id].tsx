import { useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { api, ApiError } from "@/src/api/client";
import type { RaceDetail } from "@/src/api/types";
import { HorseNumbers } from "@/src/components/HorseNumbers";
import { Screen } from "@/src/components/Screen";
import { StatusChip } from "@/src/components/StatusChip";
import { useSettings } from "@/src/context/SettingsContext";
import { colors, fonts } from "@/src/theme/colors";

export default function RaceDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { apiBaseUrl } = useSettings();
  const [race, setRace] = useState<RaceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      setRace(await api.raceDetail(apiBaseUrl, id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar carrera");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, id]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <Screen
      title={race ? `${race.track_code} R${race.race_number}` : "Carrera"}
      subtitle={race?.distance || undefined}
      loading={loading}
      error={error}
      onRetry={load}
      onRefresh={load}
      refreshing={false}
    >
      {race ? (
        <>
          <StatusChip status={race.status} mtp={race.minutes_to_post} />
          {!!race.vip_picks?.length && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Picks VIP</Text>
              {race.vip_picks.map((p) => (
                <View key={p.pick_window} style={styles.pickRow}>
                  <Text style={styles.label}>{p.pick_window_label}</Text>
                  <HorseNumbers numbers={p.selections} />
                </View>
              ))}
            </View>
          )}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Participantes</Text>
            {race.runners?.length ? (
              race.runners.map((r) => (
                <View key={r.program_number} style={styles.runner}>
                  <Text style={styles.prog}>#{r.program_number}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.horse}>
                      {r.horse_name}
                      {r.scratched ? " (retirado)" : ""}
                    </Text>
                    <Text style={styles.meta}>
                      {r.jockey || "—"} · ML {r.morning_line_odds || "—"}
                    </Text>
                  </View>
                </View>
              ))
            ) : (
              <Text style={styles.meta}>Sin participantes cargados.</Text>
            )}
          </View>
          {!!race.top_three?.length && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Llegada</Text>
              <HorseNumbers
                numbers={race.top_three.map((t) => t.program_number)}
              />
            </View>
          )}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: { marginTop: 22, gap: 8 },
  sectionTitle: {
    fontFamily: fonts.bodySemi,
    color: colors.goldSoft,
    letterSpacing: 1,
    textTransform: "uppercase",
    fontSize: 12,
  },
  pickRow: { gap: 4, marginBottom: 6 },
  label: { fontFamily: fonts.body, color: colors.muted, fontSize: 13 },
  runner: {
    flexDirection: "row",
    gap: 10,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  prog: {
    fontFamily: fonts.display,
    fontSize: 24,
    color: colors.gold,
    width: 40,
  },
  horse: { fontFamily: fonts.bodySemi, color: colors.cream, fontSize: 15 },
  meta: { fontFamily: fonts.body, color: colors.muted, fontSize: 13 },
});
