import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/src/api/client";
import { useSettings } from "@/src/context/SettingsContext";

export function useApiQuery<T>(
  fetcher: (baseUrl: string, trackCode: string) => Promise<T>,
  deps: unknown[] = []
) {
  const { ready, apiBaseUrl, trackCode } = useSettings();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (isRefresh = false) => {
      if (!ready) return;
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const result = await fetcher(apiBaseUrl, trackCode);
        setData(result);
      } catch (e) {
        const msg =
          e instanceof ApiError
            ? e.message
            : e instanceof Error
              ? e.message
              : "Error desconocido";
        setError(msg);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [ready, apiBaseUrl, trackCode, ...deps]
  );

  useEffect(() => {
    load(false);
  }, [load]);

  return {
    data,
    error,
    loading: !ready || loading,
    refreshing,
    reload: () => load(false),
    refresh: () => load(true),
    trackCode,
    apiBaseUrl,
  };
}
