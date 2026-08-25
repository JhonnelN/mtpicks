import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, fonts } from "@/src/theme/colors";

export function HorseNumbers({
  numbers,
  accent = "gold",
}: {
  numbers?: string[] | null;
  accent?: "gold" | "cream" | "success";
}) {
  if (!numbers?.length) {
    return <Text style={styles.empty}>—</Text>;
  }
  const tone =
    accent === "success"
      ? colors.success
      : accent === "cream"
        ? colors.cream
        : colors.gold;
  return (
    <View style={styles.row}>
      {numbers.map((n, i) => (
        <View
          key={`${n}-${i}`}
          style={[styles.chip, { borderColor: tone }]}
        >
          <Text style={[styles.num, { color: tone }]}>{n}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: {
    minWidth: 34,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    alignItems: "center",
  },
  num: {
    fontFamily: fonts.bodyBold,
    fontSize: 16,
  },
  empty: {
    fontFamily: fonts.body,
    color: colors.muted,
    fontSize: 16,
  },
});
