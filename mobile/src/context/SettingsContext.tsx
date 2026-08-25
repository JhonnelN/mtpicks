import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Crypto from "expo-crypto";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { DEFAULT_API_BASE } from "@/src/api/client";

const KEYS = {
  apiBaseUrl: "vip.apiBaseUrl",
  trackCode: "vip.trackCode",
  deviceId: "vip.deviceId",
} as const;

type SettingsContextValue = {
  ready: boolean;
  apiBaseUrl: string;
  trackCode: string;
  deviceId: string;
  setApiBaseUrl: (url: string) => Promise<void>;
  setTrackCode: (code: string) => Promise<void>;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);

async function ensureDeviceId(): Promise<string> {
  const existing = await AsyncStorage.getItem(KEYS.deviceId);
  if (existing) return existing;
  const id = Crypto.randomUUID();
  await AsyncStorage.setItem(KEYS.deviceId, id);
  return id;
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [apiBaseUrl, setApiBaseUrlState] = useState(DEFAULT_API_BASE);
  const [trackCode, setTrackCodeState] = useState("GP");
  const [deviceId, setDeviceId] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [url, track, device] = await Promise.all([
        AsyncStorage.getItem(KEYS.apiBaseUrl),
        AsyncStorage.getItem(KEYS.trackCode),
        ensureDeviceId(),
      ]);
      if (cancelled) return;
      if (url) setApiBaseUrlState(url);
      if (track) setTrackCodeState(track);
      setDeviceId(device);
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const setApiBaseUrl = useCallback(async (url: string) => {
    const cleaned = url.trim().replace(/\/+$/, "");
    setApiBaseUrlState(cleaned);
    await AsyncStorage.setItem(KEYS.apiBaseUrl, cleaned);
  }, []);

  const setTrackCode = useCallback(async (code: string) => {
    const next = code.trim().toUpperCase();
    setTrackCodeState(next);
    await AsyncStorage.setItem(KEYS.trackCode, next);
  }, []);

  const value = useMemo(
    () => ({
      ready,
      apiBaseUrl,
      trackCode,
      deviceId,
      setApiBaseUrl,
      setTrackCode,
    }),
    [ready, apiBaseUrl, trackCode, deviceId, setApiBaseUrl, setTrackCode]
  );

  return (
    <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) {
    throw new Error("useSettings must be used within SettingsProvider");
  }
  return ctx;
}
