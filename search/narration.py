"""
ElevenLabs voice narration for search results.
Generates a summary sentence and optionally an audio URL.
"""

import httpx
import uuid
from pathlib import Path
from backend.config import settings
from backend.models import PhotoMetadata


def _build_narration_text(query: str, photos: list[PhotoMetadata]) -> str:
    count = len(photos)
    if count == 0:
        return "I couldn't find any photos matching that description."

    emotions: list[str] = []
    for photo in photos[:5]:
        for e in photo.emotions:
            emotions.append(e.dominant)

    dominant_emotion = max(set(emotions), key=emotions.count) if emotions else None

    base = "I found 1 photo" if count == 1 else f"I found {count} photos"
    parts = [base]
    if dominant_emotion and dominant_emotion != "neutral":
        parts.append(f"where you look {dominant_emotion}")

    return " ".join(parts) + "."


async def generate_narration(query: str, photos: list[PhotoMetadata]) -> tuple[str, str | None]:
    text = _build_narration_text(query, photos)

    if not settings.elevenlabs_api_key:
        return text, None

    try:
        audio_bytes = await _call_elevenlabs(text)
        audio_url = _store_audio_locally(audio_bytes)
        return text, audio_url
    except Exception as exc:
        print(f"[narration] ElevenLabs error: {exc}")
        return text, None


async def _call_elevenlabs(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.content


def _store_audio_locally(audio_bytes: bytes) -> str:
    narration_dir = Path(settings.upload_dir) / "narration"
    narration_dir.mkdir(parents=True, exist_ok=True)
    key = f"{uuid.uuid4()}.mp3"
    (narration_dir / key).write_bytes(audio_bytes)
    return f"/uploads/narration/{key}"
