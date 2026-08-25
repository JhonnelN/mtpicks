import FontAwesome from "@expo/vector-icons/FontAwesome";
import { Tabs } from "expo-router";
import React from "react";

import { colors, fonts } from "@/src/theme/colors";

function TabIcon(props: {
  name: React.ComponentProps<typeof FontAwesome>["name"];
  color: string;
}) {
  return (
    <FontAwesome size={22} style={{ marginBottom: -2 }} name={props.name} color={props.color} />
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.gold,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          backgroundColor: colors.bgElevated,
          borderTopColor: colors.line,
        },
        tabBarLabelStyle: {
          fontFamily: fonts.bodySemi,
          fontSize: 11,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Hoy",
          tabBarIcon: ({ color }) => (
            <TabIcon name="calendar" color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="picks"
        options={{
          title: "Picks",
          tabBarIcon: ({ color }) => (
            <TabIcon name="lightbulb-o" color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="vip"
        options={{
          title: "VIP",
          tabBarIcon: ({ color }) => (
            <TabIcon name="diamond" color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="results"
        options={{
          title: "Resultados",
          tabBarIcon: ({ color }) => (
            <TabIcon name="trophy" color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="more"
        options={{
          title: "Más",
          tabBarIcon: ({ color }) => (
            <TabIcon name="bars" color={String(color)} />
          ),
        }}
      />
    </Tabs>
  );
}
