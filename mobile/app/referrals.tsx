import React, { useCallback, useEffect, useState } from "react";
import {
  Pressable,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api, ApiError } from "@/src/api/client";
import type { ReferralProfile } from "@/src/api/types";
import { Screen } from "@/src/components/Screen";
import { useSettings } from "@/src/context/SettingsContext";
import { colors, fonts } from "@/src/theme/colors";

export default function ReferralsScreen() {
  const { apiBaseUrl, deviceId } = useSettings();
  const [profile, setProfile] = useState<ReferralProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [claimMsg, setClaimMsg] = useState<string | null>(null);
  const [claiming, setClaiming] = useState(false);

  const load = useCallback(async () => {
    if (!deviceId) return;
    setLoading(true);
    setError(null);
    try {
      setProfile(await api.referralMe(apiBaseUrl, deviceId));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error de referidos");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, deviceId]);

  useEffect(() => {
    load();
  }, [load]);

  const onShare = async () => {
    if (!profile) return;
    await Share.share({
      message: profile.share_text || `Usa mi código ${profile.code}`,
      url: profile.share_url,
    });
  };

  const onClaim = async () => {
    setClaiming(true);
    setClaimMsg(null);
    try {
      const result = await api.claimReferral(apiBaseUrl, deviceId, code);
      setProfile(result.referee);
      setClaimMsg(
        `Código canjeado. +${result.rewards.referee_credits} créditos.`
      );
      setCode("");
    } catch (e) {
      setClaimMsg(e instanceof ApiError ? e.message : "No se pudo canjear");
    } finally {
      setClaiming(false);
    }
  };

  return (
    <Screen
      title="Referidos"
      subtitle="Invita y gana créditos / días VIP"
      loading={loading}
      error={error}
      onRetry={load}
      onRefresh={load}
    >
      {profile ? (
        <>
          <Text style={styles.label}>Tu código</Text>
          <Text style={styles.code}>{profile.code}</Text>
          <View style={styles.stats}>
            <Text style={styles.stat}>Créditos: {profile.credits}</Text>
            <Text style={styles.stat}>Días VIP: {profile.vip_days}</Text>
            <Text style={styles.stat}>
              Referidos: {profile.stats?.total ?? 0}
            </Text>
          </View>
          <Pressable style={styles.primary} onPress={onShare}>
            <Text style={styles.primaryText}>Compartir</Text>
          </Pressable>

          <Text style={[styles.label, { marginTop: 28 }]}>
            Canjear código de un amigo
          </Text>
          <TextInput
            value={code}
            onChangeText={setCode}
            autoCapitalize="characters"
            placeholder="AHRXXXXXX"
            placeholderTextColor={colors.muted}
            style={styles.input}
          />
          <Pressable
            style={[styles.primary, claiming && { opacity: 0.6 }]}
            onPress={onClaim}
            disabled={claiming || !code.trim()}
          >
            <Text style={styles.primaryText}>
              {claiming ? "Canjeando…" : "Canjear"}
            </Text>
          </Pressable>
          {claimMsg ? <Text style={styles.msg}>{claimMsg}</Text> : null}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: {
    fontFamily: fonts.bodySemi,
    color: colors.muted,
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  code: {
    fontFamily: fonts.display,
    fontSize: 48,
    color: colors.gold,
    marginTop: 4,
    marginBottom: 12,
  },
  stats: { gap: 4, marginBottom: 16 },
  stat: { fontFamily: fonts.body, color: colors.cream, fontSize: 16 },
  primary: {
    borderWidth: 1,
    borderColor: colors.gold,
    paddingVertical: 12,
    alignItems: "center",
    backgroundColor: colors.bgElevated,
  },
  primaryText: {
    fontFamily: fonts.bodySemi,
    color: colors.gold,
    fontSize: 15,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    color: colors.cream,
    fontFamily: fonts.bodySemi,
    fontSize: 18,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginVertical: 10,
    backgroundColor: colors.bgElevated,
  },
  msg: {
    marginTop: 10,
    fontFamily: fonts.body,
    color: colors.goldSoft,
    fontSize: 14,
  },
});
