import os
import sys
from pathlib import Path
import requests
from fastapi import APIRouter, Form, HTTPException

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from db import get_photo_by_id
from gemini_service import generate_description

router = APIRouter()
UPLOAD_DIR = Path("uploads")
NARRATION_DIR = Path("uploads/narrations")


@router.post("/narrate/")
def narrate_photo(photo_id: str = Form(...), user_id: str = Form(...)):
    try:
        # 1. Fetch photo metadata from SQLite
        photo = get_photo_by_id(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")

        objects = [o["label"] for o in (photo.get("detected_objects") or []) if isinstance(o, dict)]
        emotions = [e.get("dominant_emotion", "") for e in (photo.get("emotions") or []) if isinstance(e, dict)]

        # 2. Read the local image file
        local_image_path = UPLOAD_DIR / f"{photo_id}.jpg"
        if not local_image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image file not found for {photo_id}")

        image_bytes = local_image_path.read_bytes()

        # 3. Generate description via Gemini (falls back to labels if quota exceeded)
        description = generate_description(image_bytes, objects, emotions)

        # 4. Generate audio via ElevenLabs
        voice_id = "EXAVITQu4vr4xnSDxMaL"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        audio_filename = f"{photo_id}_narrate.mp3"
        audio_path = NARRATION_DIR / audio_filename

        headers = {"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "")}
        payload = {
            "text": description,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        r = requests.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            print(f"[narrate] ElevenLabs failed {r.status_code}: {r.text[:200]}")
            raise HTTPException(status_code=502, detail=f"ElevenLabs failed: {r.text[:200]}")

        audio_path.write_bytes(r.content)

        return {
            "description": description,
            "audio_url": f"/uploads/narrations/{audio_filename}",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[narrate] unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
