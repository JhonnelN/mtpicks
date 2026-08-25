import { Link } from "expo-router";
import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";

import { colors, fonts } from "@/src/theme/colors";

export function TrackPickerButton({ code }: { code: string }) {
  return (
    <Link href="/track-select" asChild>
      <Pressable style={styles.btn}>
        <Text style={styles.label}>PISTA</Text>
        <Text style={styles.code}>{code || "—"}</Text>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  btn: {
    borderWidth: 1,
    borderColor: colors.gold,
    paddingHorizontal: 12,
    paddingVertical: 8,
    minWidth: 72,
    alignItems: "center",
    backgroundColor: colors.bgElevated,
  },
  label: {
    fontFamily: fonts.body,
    color: colors.muted,
    fontSize: 10,
    letterSpacing: 1,
  },
  code: {
    fontFamily: fonts.display,
    color: colors.gold,
    fontSize: 22,
    lineHeight: 24,
  },
});
