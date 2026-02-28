import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  Image,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { API_BASE, DEMO_USER_ID } from "@/constants/api";

type Photo = {
  id: string;
  storage_url: string;
  caption?: string;
  importance_score?: number;
  low_value_flags?: string[];
};

export default function CleanupScreen() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLowValuePhotos = useCallback(async () => {
    setLoading(true);
    try {
      // Search for low-value photos using a generic query with exclude_low_value=false approach
      const resp = await fetch(`${API_BASE}/search/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: "screenshot blurry dark duplicate low quality",
          user_id: DEMO_USER_ID,
          limit: 50,
        }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      // Show only low-importance photos
      const lowValue = (data.photos as Photo[]).filter(
        (p) => (p.importance_score ?? 1) < 0.5 || (p.low_value_flags ?? []).length > 0
      );
      setPhotos(lowValue);
    } catch (err: any) {
      Alert.alert("Error", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchLowValuePhotos();
    }, [fetchLowValuePhotos])
  );

  function getImageUrl(url: string) {
    if (url.startsWith("http")) return url;
    return `${API_BASE}${url}`;
  }

  function confirmDelete(photo: Photo) {
    Alert.alert(
      "Delete photo?",
      "Remove this low-quality photo from your roll?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () => setPhotos((prev) => prev.filter((p) => p.id !== photo.id)),
        },
      ]
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cleanup</Text>
      <Text style={styles.subtitle}>Low-value photos detected by AI</Text>

      {loading && <ActivityIndicator color="#6c63ff" style={{ marginTop: 30 }} />}

      {!loading && photos.length === 0 && (
        <Text style={styles.empty}>
          No low-value photos found.{"\n"}Great — your camera roll looks clean!
        </Text>
      )}

      <FlatList
        data={photos}
        keyExtractor={(item) => item.id}
        numColumns={2}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Image source={{ uri: getImageUrl(item.storage_url) }} style={styles.thumb} />
            <View style={styles.infoRow}>
              <Text style={styles.score}>
                Score: {((item.importance_score ?? 1) * 100).toFixed(0)}%
              </Text>
              {(item.low_value_flags ?? []).length > 0 && (
                <Text style={styles.flags}>{(item.low_value_flags ?? []).join(", ")}</Text>
              )}
            </View>
            <TouchableOpacity style={styles.deleteBtn} onPress={() => confirmDelete(item)}>
              <Text style={styles.deleteBtnText}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
        contentContainerStyle={{ paddingBottom: 40 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0a", paddingTop: 60, paddingHorizontal: 12 },
  title: { fontSize: 24, fontWeight: "700", color: "#fff", marginBottom: 4 },
  subtitle: { fontSize: 13, color: "#666", marginBottom: 20 },
  empty: { color: "#555", textAlign: "center", marginTop: 60, fontSize: 15, lineHeight: 22 },
  card: {
    flex: 1,
    backgroundColor: "#1a1a1a",
    margin: 5,
    borderRadius: 10,
    overflow: "hidden",
  },
  thumb: { width: "100%", aspectRatio: 1, backgroundColor: "#222" },
  infoRow: { padding: 8 },
  score: { color: "#e05", fontSize: 12, fontWeight: "600" },
  flags: { color: "#888", fontSize: 11, marginTop: 2 },
  deleteBtn: {
    backgroundColor: "#3a0a0a",
    paddingVertical: 8,
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "#2a0a0a",
  },
  deleteBtnText: { color: "#e05", fontWeight: "600", fontSize: 13 },
});
