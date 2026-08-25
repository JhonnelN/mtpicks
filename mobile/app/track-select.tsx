import { router } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { api, ApiError } from "@/src/api/client";
import type { Track } from "@/src/api/types";
import { useSettings } from "@/src/context/SettingsContext";
import { colors, fonts } from "@/src/theme/colors";

export default function TrackSelectScreen() {
  const { apiBaseUrl, trackCode, setTrackCode } = useSettings();
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTracks(await api.tracks(apiBaseUrl));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar pistas");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <View style={styles.container}>
      {loading ? (
        <ActivityIndicator color={colors.gold} style={{ marginTop: 40 }} />
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.error}>{error}</Text>
          <Pressable onPress={load}>
            <Text style={styles.retry}>Reintentar</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          data={tracks}
          keyExtractor={(item) => item.code}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => {
            const active = item.code === trackCode;
            return (
              <Pressable
                style={[styles.row, active && styles.rowActive]}
                onPress={async () => {
                  await setTrackCode(item.code);
                  router.back();
                }}
              >
                <Text style={styles.code}>{item.code}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.name}>{item.name}</Text>
                  <Text style={styles.meta}>
                    {item.state} · {item.country}
                  </Text>
                </View>
              </Pressable>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { padding: 24, alignItems: "center", gap: 12 },
  error: { fontFamily: fonts.body, color: colors.danger, textAlign: "center" },
  retry: { fontFamily: fonts.bodySemi, color: colors.gold },
  row: {
    flexDirection: "row",
    gap: 14,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
    alignItems: "center",
  },
  rowActive: { backgroundColor: colors.bgSoft, paddingHorizontal: 8 },
  code: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.gold,
    width: 56,
  },
  name: { fontFamily: fonts.bodySemi, color: colors.cream, fontSize: 16 },
  meta: { fontFamily: fonts.body, color: colors.muted, fontSize: 13 },
});
