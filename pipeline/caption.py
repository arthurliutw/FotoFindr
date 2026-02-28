"""
Step 1 — Vision caption + tag extraction via Gemini.
"""

import asyncio
import base64
import json
from google import genai
from google.genai import types
from backend.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

PROMPT = """You are a photo analysis assistant.
Given an image, respond with a JSON object containing:
- "caption": a single descriptive sentence about the photo
- "tags": a list of 5-15 concise keyword tags (objects, people, places, activities, colors, mood)

Respond ONLY with valid JSON. No markdown, no explanation."""


async def get_caption_and_tags(image_bytes: bytes) -> dict:
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    response = await asyncio.to_thread(
        _client.models.generate_content,
        model="gemini-1.5-flash",
        contents=[PROMPT, image_part],
    )

    raw = response.text or "{}"
    # Strip markdown code fences if present
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"caption": raw, "tags": []}

    return {
        "caption": result.get("caption", ""),
        "tags": result.get("tags", []),
    }
