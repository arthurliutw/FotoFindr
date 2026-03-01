import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";

type Props = {
  stage: "idle" | "clearing" | "uploading" | "processing" | "ready";
  indexDone?: number;
  indexTotal?: number;
};

export default function StatusBar({ stage, indexDone = 0, indexTotal = 0 }: Props) {
  let statusLabel =
    stage === "clearing" ? "Clearing old data…" :
      stage === "uploading" ? `Uploading… ${indexDone}/${indexTotal}` :
        stage === "processing" ? "Running AI pipeline…" :
          stage === "ready" ? "Ready to search" : null;

  if (!statusLabel) return null;

  if (stage !== "ready") {
    return (
      <View style={styles.statusBar}>
        <ActivityIndicator size="small" color="#6c63ff" />
        <Text style={styles.statusText}>{statusLabel}</Text>
      </View>
    );
  }

  return <Text style={styles.statusReady}>{statusLabel}</Text>;
}

const styles = StyleSheet.create({
  statusBar: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 12 },
  statusText: { color: "#6c63ff", fontSize: 13 },
  statusReady: { color: "#4caf50", fontSize: 13, textAlign: "center", marginBottom: 12 },
});