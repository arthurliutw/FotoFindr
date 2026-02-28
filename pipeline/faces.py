"""
Step 4 — Face detection + embedding generation.
Uses MediaPipe for detection, Gemini for description + embedding.
"""

import asyncio
import io
import numpy as np
from PIL import Image
from google import genai
from backend.config import settings
from backend.db import get_or_create_person

_client = genai.Client(api_key=settings.gemini_api_key)


def _detect_faces_mediapipe(image_bytes: bytes) -> list[bytes]:
    try:
        import mediapipe as mp
    except ImportError:
        return []

    mp_face = mp.solutions.face_detection
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(img)
    h, w = img_array.shape[:2]

    face_crops = []
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as detector:
        results = detector.process(img_array)
        if not results.detections:
            return []

        for detection in results.detections:
            bb = detection.location_data.relative_bounding_box
            x1 = max(0, int(bb.xmin * w))
            y1 = max(0, int(bb.ymin * h))
            x2 = min(w, int((bb.xmin + bb.width) * w))
            y2 = min(h, int((bb.ymin + bb.height) * h))

            face_img = img.crop((x1, y1, x2, y2)).resize((224, 224))
            buf = io.BytesIO()
            face_img.save(buf, format="JPEG")
            face_crops.append(buf.getvalue())

    return face_crops


async def _embed_face(face_bytes: bytes) -> list[float]:
    from google.genai import types

    image_part = types.Part.from_bytes(data=face_bytes, mime_type="image/jpeg")
    desc_response = await asyncio.to_thread(
        _client.models.generate_content,
        model="gemini-1.5-flash",
        contents=["Describe the face features in 1-2 sentences for identification.", image_part],
    )
    description = desc_response.text or "a person"

    embed_response = await asyncio.to_thread(
        _client.models.embed_content,
        model="models/text-embedding-004",
        contents=description,
    )
    return embed_response.embeddings[0].values


async def detect_and_cluster_faces(image_bytes: bytes, user_id: str) -> list[str]:
    face_crops = _detect_faces_mediapipe(image_bytes)
    if not face_crops:
        return []

    person_ids = []
    for face_bytes in face_crops:
        embedding = await _embed_face(face_bytes)
        person_id = get_or_create_person(user_id, embedding)
        person_ids.append(person_id)

    return list(set(person_ids))
