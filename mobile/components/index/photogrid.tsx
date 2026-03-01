import React from "react";
import { FlatList, Pressable, Text, StyleSheet } from "react-native";
import { Image } from "expo-image";

export type LocalPhoto = {
  assetId: string;
  uri: string;
};

type Props = {
  photos: LocalPhoto[];
  onPhotoPress: (photoId: LocalPhoto) => void;
  loadMore: () => void;
  filter: string[];
  photoIdMap: Record<string, string>;
};

export default function PhotoGrid({ photos, photoIdMap, onPhotoPress, loadMore, filter }: Props) {
  const filteredPhotos = filter.length > 0
    ? photos.filter(photo => filter.includes(photoIdMap[photo.assetId]))

    : photos;

  return (
    <FlatList
      data={filteredPhotos}
      keyExtractor={(item) => item.assetId}
      numColumns={3}
      renderItem={({ item }) => (
        <Pressable onPress={() => onPhotoPress(item)} style={{ flex: 1 / 3 }}>
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