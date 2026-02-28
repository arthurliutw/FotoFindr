import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  TextInput,
  Modal,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { API_BASE, DEMO_USER_ID } from "@/constants/api";

type Person = {
  id: string;
  name?: string;
  photo_count: number;
  cover_photo_url?: string;
};

export default function PeopleScreen() {
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [nameInput, setNameInput] = useState("");

  const fetchPeople = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/profiles/${DEMO_USER_ID}`);
      if (!resp.ok) throw new Error(await resp.text());
      const data: Person[] = await resp.json();
      setPeople(data);
    } catch (err: any) {
      Alert.alert("Error", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchPeople();
    }, [fetchPeople])
  );

  async function saveName() {
    if (!selectedPerson || !nameInput.trim()) return;
    try {
      const resp = await fetch(`${API_BASE}/profiles/${selectedPerson.id}/name`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: nameInput.trim() }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      setPeople((prev) =>
        prev.map((p) => (p.id === selectedPerson.id ? { ...p, name: nameInput.trim() } : p))
      );
      setModalVisible(false);
    } catch (err: any) {
      Alert.alert("Error saving name", err.message);
    }
  }

  function openNaming(person: Person) {
    setSelectedPerson(person);
    setNameInput(person.name ?? "");
    setModalVisible(true);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>People</Text>
      <Text style={styles.subtitle}>Face clusters detected in your photos</Text>

      {loading && <ActivityIndicator color="#6c63ff" style={{ marginTop: 30 }} />}

      {!loading && people.length === 0 && (
        <Text style={styles.empty}>No people detected yet. Upload some photos first.</Text>
      )}

      <FlatList
        data={people}
        keyExtractor={(item) => item.id}
        numColumns={2}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => openNaming(item)}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {item.name ? item.name[0].toUpperCase() : "?"}
              </Text>
            </View>
            <Text style={styles.personName}>{item.name ?? "Unknown"}</Text>
            <Text style={styles.photoCount}>{item.photo_count} photo{item.photo_count !== 1 ? "s" : ""}</Text>
            <Text style={styles.tapHint}>Tap to name</Text>
          </TouchableOpacity>
        )}
        contentContainerStyle={{ paddingBottom: 40 }}
      />

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Name this person</Text>
            <TextInput
              style={styles.modalInput}
              value={nameInput}
              onChangeText={setNameInput}
              placeholder="Enter name..."
              placeholderTextColor="#777"
              autoFocus
            />
            <View style={styles.modalBtns}>
              <TouchableOpacity
                style={[styles.modalBtn, styles.cancelBtn]}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.modalBtn, styles.saveBtn]} onPress={saveName}>
                <Text style={styles.saveBtnText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0a", paddingTop: 60, paddingHorizontal: 16 },
  title: { fontSize: 24, fontWeight: "700", color: "#fff", marginBottom: 4 },
  subtitle: { fontSize: 13, color: "#666", marginBottom: 20 },
  empty: { color: "#555", textAlign: "center", marginTop: 60, fontSize: 15 },
  card: {
    flex: 1,
    backgroundColor: "#1a1a1a",
    margin: 6,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#6c63ff",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 10,
  },
  avatarText: { fontSize: 28, color: "#fff", fontWeight: "700" },
  personName: { color: "#fff", fontSize: 16, fontWeight: "600", textAlign: "center" },
  photoCount: { color: "#888", fontSize: 12, marginTop: 2 },
  tapHint: { color: "#444", fontSize: 11, marginTop: 4 },
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.7)", justifyContent: "flex-end" },
  modalCard: { backgroundColor: "#1a1a1a", borderRadius: 20, padding: 24, margin: 16 },
  modalTitle: { color: "#fff", fontSize: 18, fontWeight: "700", marginBottom: 16 },
  modalInput: {
    backgroundColor: "#0a0a0a",
    borderRadius: 10,
    color: "#fff",
    padding: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: "#333",
    marginBottom: 20,
  },
  modalBtns: { flexDirection: "row", gap: 12 },
  modalBtn: { flex: 1, borderRadius: 10, paddingVertical: 14, alignItems: "center" },
  cancelBtn: { backgroundColor: "#2a2a2a" },
  saveBtn: { backgroundColor: "#6c63ff" },
  cancelBtnText: { color: "#aaa", fontWeight: "600" },
  saveBtnText: { color: "#fff", fontWeight: "600" },
});
