import React from "react";
import { FlatList, Pressable, Text, StyleSheet } from "react-native";
import { Image } from "expo-image";

type LocalPhoto = { id: string; uri: string };

type Props = {
  photos: LocalPhoto[];
  onPhotoPress: (uri: string) => void;
  loadMore: () => void;
};

export default function PhotoGrid({ photos, onPhotoPress, loadMore }: Props) {
  return (
    <FlatList
      data={photos}
      keyExtractor={(item) => item.id}
      numColumns={3}
      renderItem={({ item }) => (
        <Pressable onPress={() => onPhotoPress(item.uri)} style={{ flex: 1 / 3 }}>
          <Image source={{ uri: item.uri }} style={styles.thumb} />
        </Pressable>
      )}
      contentContainerStyle={styles.grid}
      ListFooterComponent={photos.length > 0 ? (
        <Pressable onPress={loadMore}>
          <Text style={styles.loadMoreButton}>Load More</Text>
        </Pressable>
      ) : null}
      ListFooterComponentStyle={{ paddingBottom: 30 }}
    />
  );
}

const styles = StyleSheet.create({
  grid: { gap: 2 },
  thumb: { aspectRatio: 1, margin: 1, borderRadius: 4 },
  loadMoreButton: { color: "#6c63ff", textAlign: "center", marginTop: 16, fontSize: 14, fontWeight: "600" },
});