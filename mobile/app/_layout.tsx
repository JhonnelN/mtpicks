import {
  BebasNeue_400Regular,
  useFonts as useBebas,
} from "@expo-google-fonts/bebas-neue";
import {
  SourceSans3_400Regular,
  SourceSans3_600SemiBold,
  SourceSans3_700Bold,
  useFonts as useSourceSans,
} from "@expo-google-fonts/source-sans-3";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import "react-native-reanimated";

import { SettingsProvider } from "@/src/context/SettingsContext";
import { colors } from "@/src/theme/colors";

export { ErrorBoundary } from "expo-router";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [bebasLoaded] = useBebas({ BebasNeue_400Regular });
  const [sansLoaded] = useSourceSans({
    SourceSans3_400Regular,
    SourceSans3_600SemiBold,
    SourceSans3_700Bold,
  });
  const loaded = bebasLoaded && sansLoaded;

  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);

  if (!loaded) return null;

  return (
    <SettingsProvider>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.bg },
          headerTintColor: colors.gold,
          headerTitleStyle: { fontFamily: "SourceSans3_600SemiBold" },
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="track-select"
          options={{ presentation: "modal", title: "Elegir hipódromo" }}
        />
        <Stack.Screen name="race/[id]" options={{ title: "Carrera" }} />
        <Stack.Screen name="referrals" options={{ title: "Referidos" }} />
        <Stack.Screen name="settings" options={{ title: "Ajustes API" }} />
      </Stack>
    </SettingsProvider>
  );
}
