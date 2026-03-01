// components/index/PhotoModal.tsx
import React, { useEffect, useState } from "react";
import { View, Text, Modal, Pressable, StyleSheet, FlatList, ActivityIndicator } from "react-native";
import { Image } from "expo-image";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Audio } from "expo-av";
import { API_BASE, DEMO_USER_ID } from "@/constants/api";

type Props = {
  visible: boolean;
  imageUri: string | null;
  labels?: string[];
  onClose: () => void;
};

export default function PhotoModal({ visible, imageUri, onClose }: Props) {
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [loading, setLoading] = useState(false);

  console.log('imageuri is', imageUri);

  if (!imageUri) return null;

  async function handleNarrate() {
    if (!imageUri) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("device_uri", imageUri);
      formData.append("user_id", DEMO_USER_ID);

      const res = await fetch(`${API_BASE}/narrate/`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.audio_url) {
        if (sound) {
          await sound.unloadAsync();
        }
        const { sound: newSound } = await Audio.Sound.createAsync({
          uri: `${API_BASE}${data.audio_url}`,
        });
        setSound(newSound);
        await newSound.playAsync();
      }
    } catch (e) {
      console.error("Narrate failed", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.modalContainer}>
        <View style={styles.modalContent}>
          <Pressable onPress={onClose} style={styles.modalImage}>
            <Image source={{ uri: imageUri }} style={styles.modalImage} />
          </Pressable>
          <View style={styles.descriptionSection}>
            {/* <View style={styles.labelsContainer}>
              {labels.map((label, idx) => (
                <Text key={idx} style={styles.label}>{label}</Text>
              ))}
            </View> */}
            <ImageLabelsScreen imageId={imageUri.split(".")[0]} />
            <Pressable style={styles.narrateButton} onPress={handleNarrate}>
              <IconSymbol size={14} name="speaker.wave.2" color="#ddd" />
              <Text style={styles.narrateButtonText}>{loading ? "Loading..." : "Narrate"}</Text>
              <Text>{imageUri}</Text>
            </Pressable>
          </View>
        </View>
        <Pressable style={styles.closeButton} onPress={onClose}>
          <Text style={styles.closeButtonText}>✕</Text>
        </Pressable>
      </View>
    </Modal>
  );
}
interface ImageLabelsResponse {
  image_id: string;
  labels: string[];
}


function ImageLabelsScreen({ imageId }: { imageId: string }) {
  const [labels, setLabels] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLabels = async () => {
      try {
        const response = await fetch(`${API_BASE}/image_labels/?image_id=${imageId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: ImageLabelsResponse = await response.json();
        setLabels(data.labels || []);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Unknown error");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchLabels();
  }, [imageId]);

  if (loading) {
    return (
      <View style={styles.labelsContainer}>
        <ActivityIndicator size="large" />
        <Text>Loading labels...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.labelsContainer}>
        <Text style={{ color: "red" }}>Error: {error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.labelsContainer}>
      {labels.map((label, idx) => (
        <Text key={idx} style={styles.label}>{label}</Text>
      ))}
    </View>
  );
};


const styles = StyleSheet.create({
  modalContainer: { width: "100%", flex: 1, backgroundColor: "rgba(0,0,0,0.9)", justifyContent: "center", alignItems: "center" },
  modalContent: { flex: 1, justifyContent: "flex-start", alignItems: "center", width: "100%", paddingVertical: 10 },
  modalImage: { flex: 10, width: "100%", resizeMode: "contain" },
  descriptionSection: { flex: 2, width: "100%", padding: 16, backgroundColor: "rgba(0,0,0,0.7)" },
  labelsContainer: { flexDirection: "row", gap: 8, flexWrap: "wrap" },
  label: { backgroundColor: "#6c63ff", color: "#fff", paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, fontSize: 12 },
  narrateButton: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 12, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, backgroundColor: "#444" },
  narrateButtonText: { color: "#ddd", fontSize: 14, fontWeight: "600" },
  closeButton: { position: "absolute", top: 40, right: 20, zIndex: 1 },
  closeButtonText: { color: "#fff", fontSize: 32, fontWeight: "bold" },
});