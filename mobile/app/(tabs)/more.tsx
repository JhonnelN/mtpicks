import { Link } from "expo-router";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Screen } from "@/src/components/Screen";
import { useSettings } from "@/src/context/SettingsContext";
import { colors, fonts } from "@/src/theme/colors";

export default function MoreScreen() {
  const { apiBaseUrl, trackCode, deviceId } = useSettings();

  return (
    <Screen title="Más" subtitle="Referidos y configuración">
      <Text style={styles.meta}>Pista: {trackCode}</Text>
      <Text style={styles.meta} numberOfLines={1}>
        API: {apiBaseUrl}
      </Text>
      <Text style={styles.meta} numberOfLines={1}>
        Device: {deviceId.slice(0, 18)}…
      </Text>

      <View style={styles.menu}>
        <Link href="/referrals" asChild>
          <Pressable style={styles.item}>
            <Text style={styles.itemTitle}>Referidos</Text>
            <Text style={styles.itemSub}>Código, créditos y canjear invite</Text>
          </Pressable>
        </Link>
        <Link href="/settings" asChild>
          <Pressable style={styles.item}>
            <Text style={styles.itemTitle}>Ajustes API</Text>
            <Text style={styles.itemSub}>URL del backend y prueba de health</Text>
          </Pressable>
        </Link>
        <Link href="/track-select" asChild>
          <Pressable style={styles.item}>
            <Text style={styles.itemTitle}>Cambiar hipódromo</Text>
            <Text style={styles.itemSub}>Seleccionar pista activa</Text>
          </Pressable>
        </Link>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  meta: {
    fontFamily: fonts.body,
    color: colors.muted,
    fontSize: 13,
    marginBottom: 4,
  },
  menu: { marginTop: 20, gap: 2 },
  item: {
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  itemTitle: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.cream,
  },
  itemSub: {
    fontFamily: fonts.body,
    color: colors.muted,
    fontSize: 14,
    marginTop: 2,
  },
});
