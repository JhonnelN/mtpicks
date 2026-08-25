import React, { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { api, ApiError, DEFAULT_API_BASE } from "@/src/api/client";
import { Screen } from "@/src/components/Screen";
import { useSettings } from "@/src/context/SettingsContext";
import { colors, fonts } from "@/src/theme/colors";

const PRESETS = [
  { label: "Emulador Android → PC", url: DEFAULT_API_BASE },
  { label: "Localhost (web/iOS sim)", url: "http://127.0.0.1:8000/api" },
  {
    label: "Dispositivo en LAN (edita IP)",
    url: "http://192.168.1.10:8000/api",
  },
];

export default function SettingsScreen() {
  const { apiBaseUrl, setApiBaseUrl } = useSettings();
  const [draft, setDraft] = useState(apiBaseUrl);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const save = async () => {
    await setApiBaseUrl(draft);
    setStatus("URL guardada.");
  };

  const test = async () => {
    setBusy(true);
    setStatus(null);
    try {
      const url = draft.trim().replace(/\/+$/, "");
      const health = await api.health(url);
      await setApiBaseUrl(url);
      setStatus(`OK · ${health.service} · ${health.status}`);
    } catch (e) {
      setStatus(e instanceof ApiError ? e.message : "Falló la conexión");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen
      title="Ajustes"
      subtitle="URL base del API Django (termina en /api)"
    >
      <Text style={styles.label}>API base URL</Text>
      <TextInput
        value={draft}
        onChangeText={setDraft}
        autoCapitalize="none"
        autoCorrect={false}
        placeholder="https://….trycloudflare.com/api"
        placeholderTextColor={colors.muted}
        style={styles.input}
      />
      <View style={styles.actions}>
        <Pressable style={styles.btn} onPress={save}>
          <Text style={styles.btnText}>Guardar</Text>
        </Pressable>
        <Pressable
          style={[styles.btn, styles.btnSolid, busy && { opacity: 0.6 }]}
          onPress={test}
          disabled={busy}
        >
          <Text style={[styles.btnText, styles.btnSolidText]}>
            {busy ? "Probando…" : "Probar health"}
          </Text>
        </Pressable>
      </View>
      {status ? <Text style={styles.status}>{status}</Text> : null}

      <Text style={[styles.label, { marginTop: 28 }]}>Presets</Text>
      {PRESETS.map((p) => (
        <Pressable
          key={p.label}
          style={styles.preset}
          onPress={() => setDraft(p.url)}
        >
          <Text style={styles.presetTitle}>{p.label}</Text>
          <Text style={styles.presetUrl}>{p.url}</Text>
        </Pressable>
      ))}
      <Text style={styles.hint}>
        En dispositivo físico usa la IP LAN de tu PC o pega la URL del túnel
        Cloudflare/ngrok + `/api`.
      </Text>
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
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    color: colors.cream,
    fontFamily: fonts.body,
    fontSize: 15,
    paddingHorizontal: 12,
    paddingVertical: 12,
    backgroundColor: colors.bgElevated,
  },
  actions: { flexDirection: "row", gap: 10, marginTop: 14 },
  btn: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.gold,
    paddingVertical: 12,
    alignItems: "center",
  },
  btnSolid: { backgroundColor: colors.gold },
  btnText: { fontFamily: fonts.bodySemi, color: colors.gold },
  btnSolidText: { color: colors.bg },
  status: {
    marginTop: 12,
    fontFamily: fonts.body,
    color: colors.goldSoft,
    fontSize: 14,
  },
  preset: {
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  presetTitle: {
    fontFamily: fonts.bodySemi,
    color: colors.cream,
    fontSize: 15,
  },
  presetUrl: { fontFamily: fonts.body, color: colors.muted, fontSize: 13 },
  hint: {
    marginTop: 18,
    fontFamily: fonts.body,
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
});
