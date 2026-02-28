import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Image } from "expo-image";
import { API_BASE, DEMO_USER_ID } from "@/constants/api";

type Photo = {
  id: string;
  storage_url: string;
  caption?: string;
};

type SearchResult = {
  photos: Photo[];
  narration_text?: string;
  total: number;
};

export default function SearchScreen() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [searched, setSearched] = useState(false);

  async function doSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const resp = await fetch(`${API_BASE}/search/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), user_id: DEMO_USER_ID, limit: 30 }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data: SearchResult = await resp.json();
      setResult(data);
    } catch (err: any) {
      Alert.alert("Search failed", err.message);
    } finally {
      setLoading(false);
    }
  }

  function getImageUrl(url: string) {
    if (url.startsWith("http")) return url;
    return `${API_BASE}${url}`;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Search</Text>
      <Text style={styles.subtitle}>Searches photos you've indexed via the Camera Roll tab</Text>

      <View style={styles.row}>
        <TextInput
          style={styles.input}
          placeholder="dog at the beach, me in a yellow sweater..."
          placeholderTextColor="#555"
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={doSearch}
          returnKeyType="search"
        />
        <TouchableOpacity style={styles.searchBtn} onPress={doSearch} disabled={loading}>
          <Text style={styles.searchBtnText}>Go</Text>
        </TouchableOpacity>
      </View>

      {loading && <ActivityIndicator color="#6c63ff" style={{ marginTop: 30 }} />}

      {!loading && result && result.total > 0 && (
        <>
          {result.narration_text ? (
            <Text style={styles.narration}>{result.narration_text}</Text>
          ) : null}
          <FlatList
            data={result.photos}
            keyExtractor={(item) => item.id}
            numColumns={3}
            renderItem={({ item }) => (
              <Image
                source={{ uri: getImageUrl(item.storage_url) }}
                style={styles.thumb}
                contentFit="cover"
              />
            )}
            contentContainerStyle={{ paddingBottom: 40 }}
          />
        </>
      )}

      {!loading && searched && result?.total === 0 && (
        <Text style={styles.empty}>
          No results for "{query}".{"\n\n"}
          Go to the Camera Roll tab and tap "Index for AI Search" to make photos searchable.
        </Text>
      )}

      {!searched && !loading && (
        <Text style={styles.hint}>
          Try: "me smiling", "dog at the park", "beach sunset"
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0a", paddingTop: 60, paddingHorizontal: 16 },
  title: { fontSize: 24, fontWeight: "700", color: "#fff", marginBottom: 4 },
  subtitle: { fontSize: 12, color: "#555", marginBottom: 16 },
  row: { flexDirection: "row", gap: 8, marginBottom: 16 },
  input: {
    flex: 1,
    backgroundColor: "#1a1a1a",
    color: "#fff",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    borderWidth: 1,
    borderColor: "#333",
  },
  searchBtn: {
    backgroundColor: "#6c63ff",
    borderRadius: 10,
    paddingHorizontal: 18,
    justifyContent: "center",
  },
  searchBtnText: { color: "#fff", fontWeight: "600", fontSize: 15 },
  narration: { color: "#aaa", fontSize: 13, marginBottom: 12, fontStyle: "italic" },
  thumb: { flex: 1 / 3, aspectRatio: 1, margin: 2, borderRadius: 6 },
  empty: { color: "#555", textAlign: "center", marginTop: 60, fontSize: 14, lineHeight: 22 },
  hint: { color: "#444", textAlign: "center", marginTop: 50, fontSize: 13, fontStyle: "italic" },
});
