import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors, fonts } from "@/src/theme/colors";

type Props = {
  title?: string;
  subtitle?: string;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  refreshing?: boolean;
  onRefresh?: () => void;
  scroll?: boolean;
};

export function Screen({
  title,
  subtitle,
  headerRight,
  children,
  loading,
  error,
  onRetry,
  refreshing,
  onRefresh,
  scroll = true,
}: Props) {
  const body = (
    <>
      {(title || headerRight) && (
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            {title ? <Text style={styles.title}>{title}</Text> : null}
            {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
          </View>
          {headerRight}
        </View>
      )}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} size="large" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.error}>{error}</Text>
          {onRetry ? (
            <Pressable style={styles.retry} onPress={onRetry}>
              <Text style={styles.retryText}>Reintentar</Text>
            </Pressable>
          ) : null}
          <Text style={styles.hint}>
            Si falla, abre Más → Ajustes y revisa la URL del API.
          </Text>
        </View>
      ) : (
        children
      )}
    </>
  );

  return (
    <LinearGradient
      colors={[colors.bg, "#08140E", "#142A1C"]}
      style={styles.flex}
      start={{ x: 0.1, y: 0 }}
      end={{ x: 0.9, y: 1 }}
    >
      <SafeAreaView style={styles.flex} edges={["top", "left", "right"]}>
        {scroll ? (
          <ScrollView
            contentContainerStyle={styles.content}
            refreshControl={
              onRefresh ? (
                <RefreshControl
                  refreshing={!!refreshing}
                  onRefresh={onRefresh}
                  tintColor={colors.gold}
                />
              ) : undefined
            }
          >
            {body}
          </ScrollView>
        ) : (
          <View style={[styles.flex, styles.content]}>{body}</View>
        )}
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  content: { paddingHorizontal: 20, paddingBottom: 32, paddingTop: 8 },
  headerRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    marginBottom: 18,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 40,
    color: colors.cream,
    letterSpacing: 1,
    lineHeight: 42,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.muted,
    marginTop: 2,
  },
  center: {
    minHeight: 220,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingHorizontal: 12,
  },
  error: {
    fontFamily: fonts.bodySemi,
    color: colors.danger,
    textAlign: "center",
    fontSize: 16,
  },
  hint: {
    fontFamily: fonts.body,
    color: colors.muted,
    textAlign: "center",
    fontSize: 13,
    marginTop: 4,
  },
  retry: {
    borderWidth: 1,
    borderColor: colors.gold,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  retryText: {
    fontFamily: fonts.bodySemi,
    color: colors.gold,
    fontSize: 14,
  },
});
