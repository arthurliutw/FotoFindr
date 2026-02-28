import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  Image,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { API_BASE, DEMO_USER_ID } from "@/constants/api";

type Photo = {
  id: string;
  storage_url: string;
  caption?: string;
  tags?: string[];
  importance_score?: number;
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

  async function doSearch() {
    if (!query.trim()) return;
    setLoading(true);
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

      <View style={styles.row}>
        <TextInput
          style={styles.input}
          placeholder="e.g. photos where I look happy"
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

      {result && !loading && (
        <>
          {result.narration_text ? (
            <Text style={styles.narration}>{result.narration_text}</Text>
          ) : null}
          <Text style={styles.count}>{result.total} photo{result.total !== 1 ? "s" : ""} found</Text>
          <FlatList
            data={result.photos}
            keyExtractor={(item) => item.id}
            numColumns={3}
            renderItem={({ item }) => (
              <View style={styles.photoWrap}>
                <Image source={{ uri: getImageUrl(item.storage_url) }} style={styles.thumb} />
                {item.caption ? (
                  <Text numberOfLines={2} style={styles.caption}>{item.caption}</Text>
                ) : null}
              </View>
            )}
            contentContainerStyle={{ paddingBottom: 40 }}
          />
        </>
      )}

      {result && result.total === 0 && !loading && (
        <Text style={styles.empty}>No photos found. Try a different query.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0a", paddingTop: 60, paddingHorizontal: 16 },
  title: { fontSize: 24, fontWeight: "700", color: "#fff", marginBottom: 16 },
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
  narration: { color: "#aaa", fontSize: 14, marginBottom: 10, fontStyle: "italic" },
  count: { color: "#666", fontSize: 13, marginBottom: 12 },
  photoWrap: { flex: 1 / 3, margin: 2 },
  thumb: { width: "100%", aspectRatio: 1, borderRadius: 6, backgroundColor: "#222" },
  caption: { color: "#888", fontSize: 10, marginTop: 2, paddingHorizontal: 2 },
  empty: { color: "#555", textAlign: "center", marginTop: 60, fontSize: 15 },
});
