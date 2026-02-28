"""
Parse natural language queries into structured metadata filters.
Simple keyword extraction — no NLP model needed for demo.
"""

import re

EMOTION_WORDS = {
    "happy": ["happy", "smiling", "smile", "laughing", "joyful", "cheerful"],
    "sad": ["sad", "crying", "upset", "unhappy"],
    "angry": ["angry", "mad", "furious", "frustrated"],
    "surprised": ["surprised", "shocked", "amazed"],
    "neutral": ["neutral", "calm", "serious"],
}

# Only filter by labels YOLO (COCO) actually detects — ignore everything else
# and let CLIP handle colour/clothing/mood naturally.
_YOLO_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag",
    "tie", "suitcase", "frisbee", "skis", "snowboard", "kite", "skateboard",
    "surfboard", "bottle", "cup", "fork", "knife", "spoon", "bowl", "banana",
    "apple", "sandwich", "orange", "broccoli", "carrot", "pizza", "donut",
    "cake", "chair", "couch", "bed", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "toothbrush",
}


def parse_filters(query: str) -> dict:
    q = query.lower()
    filters: dict = {}

    # --- "me" identity filter ---
    if re.search(r"\bme\b|\bmy\b|\bmyself\b", q):
        filters["wants_me"] = True

    # --- Named person: "of Jake", "with Jake" ---
    name_match = re.search(r"\bof\s+([A-Z][a-z]+)|\bwith\s+([A-Z][a-z]+)", query)
    if name_match:
        filters["person_name"] = name_match.group(1) or name_match.group(2)

    # --- Emotion ---
    for emotion, keywords in EMOTION_WORDS.items():
        if any(kw in q for kw in keywords):
            filters["emotion"] = emotion
            break

    # --- Object keywords: only YOLO-detectable COCO classes ---
    # Clothing/colours/moods are handled by CLIP similarity, not this filter.
    words = re.findall(r"\b[a-z]+\b", q)
    obj_keywords = [w for w in words if w in _YOLO_CLASSES]
    if obj_keywords:
        filters["objects"] = obj_keywords

    # --- Low-value filter ---
    if any(kw in q for kw in ["screenshot", "screenshots", "unimportant", "junk", "blurry", "duplicate"]):
        filters["low_value_only"] = True

    return filters
