import { Link } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "@/src/api/client";
import { HorseNumbers } from "@/src/components/HorseNumbers";
import { Screen } from "@/src/components/Screen";
import { TrackPickerButton } from "@/src/components/TrackPickerButton";
import { useApiQuery } from "@/src/hooks/useApiQuery";
import { colors, fonts } from "@/src/theme/colors";

const DIV_ORDER = ["W", "P", "S", "EXA", "TRI", "SUPER", "DD", "P3", "P4"];

export default function ResultsScreen() {
  const { data, error, loading, refreshing, refresh, reload, trackCode } =
    useApiQuery((base, track) => api.results(base, track));

  return (
    <Screen
      title="Resultados"
      subtitle={data ? `${trackCode} · ${data.date}` : trackCode}
      headerRight={<TrackPickerButton code={trackCode} />}
      loading={loading}
      error={error}
      onRetry={reload}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      {!data?.results?.length ? (
        <Text style={styles.empty}>
          Aún no hay resultados oficiales para esta pista.
        </Text>
      ) : (
        data.results.map((race) => (
          <View key={race.id} style={styles.block}>
            <Link
              href={{ pathname: "/race/[id]", params: { id: String(race.id) } }}
              asChild
            >
              <Pressable>
                <Text style={styles.race}>
                  R{race.race_number} · {race.distance || "—"}
                </Text>
                <Text style={styles.label}>Llegada</Text>
                <HorseNumbers
                  numbers={race.top_three.map((t) => t.program_number)}
                />
              </Pressable>
            </Link>
            <Text style={[styles.label, { marginTop: 10 }]}>Dividendos</Text>
            <View style={styles.divGrid}>
              {DIV_ORDER.filter((k) => race.dividends?.[k]).map((key) => {
                const d = race.dividends[key];
                return (
                  <Text key={key} style={styles.div}>
                    {key} {d.combination} ${Number(d.amount).toFixed(2)}
                  </Text>
                );
              })}
            </View>
            {!!race.video_replay_url && (
              <Pressable
                onPress={() => WebBrowser.openBrowserAsync(race.video_replay_url)}
              >
                <Text style={styles.replay}>Ver replay</Text>
              </Pressable>
            )}
          </View>
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
    gap: 6,
  },
  race: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.gold,
    marginBottom: 4,
  },
  label: {
    fontFamily: fonts.bodySemi,
    color: colors.muted,
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  divGrid: { gap: 2 },
  div: { fontFamily: fonts.body, color: colors.cream, fontSize: 14 },
  replay: {
    marginTop: 8,
    fontFamily: fonts.bodySemi,
    color: colors.gold,
    fontSize: 14,
  },
});
