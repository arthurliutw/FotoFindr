"""
Step 2 — Object detection via YOLOv8 (ultralytics).
Model weights (~6 MB) are downloaded automatically on first run.
"""

import asyncio
import io
from functools import lru_cache
from PIL import Image
from backend.models import DetectedObject


@lru_cache(maxsize=1)
def _get_model():
    from ultralytics import YOLO
    return YOLO("yolov8n.pt")


async def detect_objects(image_bytes: bytes) -> list[DetectedObject]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _detect_sync, image_bytes)


def _detect_sync(image_bytes: bytes) -> list[DetectedObject]:
    model = _get_model()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = model(img, verbose=False)

    seen: set[str] = set()
    objects: list[DetectedObject] = []
    for r in results:
        for box in r.boxes:
            label = r.names[int(box.cls[0])]
            conf = float(box.conf[0])
            if label not in seen:
                seen.add(label)
                objects.append(DetectedObject(label=label, confidence=round(conf, 3)))

    return objects
