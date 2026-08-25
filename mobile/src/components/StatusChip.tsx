import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, fonts } from "@/src/theme/colors";

const LABELS: Record<string, string> = {
  scheduled: "Programada",
  next: "Siguiente",
  running: "En curso",
  official: "Oficial",
  cancelled: "Cancelada",
  scratched: "Anulada",
};

export function StatusChip({
  status,
  mtp,
}: {
  status: string;
  mtp?: number | null;
}) {
  const label = LABELS[status] || status;
  return (
    <View style={styles.row}>
      <View style={styles.chip}>
        <Text style={styles.text}>{label}</Text>
      </View>
      {mtp != null ? (
        <Text style={styles.mtp}>
          {mtp >= 0 ? `${mtp} MTP` : `${Math.abs(mtp)} min`}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  chip: {
    borderColor: colors.line,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: colors.bgSoft,
  },
  text: {
    fontFamily: fonts.bodySemi,
    color: colors.goldSoft,
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  mtp: {
    fontFamily: fonts.bodyBold,
    color: colors.cream,
    fontSize: 13,
  },
});
