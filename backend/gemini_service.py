import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from google import genai
from google.genai import types
from config import settings

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


MODEL = "gemini-2.0-flash"


def find_matching_labels(
    query: str, object_labels: list[str], emotion_labels: list[str]
) -> list[str]:
    """Ask Gemini which object/emotion labels match the user's query."""
    if not settings.gemini_api_key:
        return []
    if not object_labels and not emotion_labels:
        return []

    prompt = f"""You are a photo search classifier.

User query: "{query}"

Available detected objects: {json.dumps(object_labels)}
Available detected emotions: {json.dumps(emotion_labels)}

Return ONLY a JSON array of items from the above lists that are relevant to the query.
Do not add items that are not in the lists. Do not explain. Just the JSON array.

Example output: ["dog", "happy"]
"""

    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"[gemini] find_matching_labels error: {e}")
        return []


def _label_fallback_description(objects: list, emotions: list) -> str:
    """Build a simple description from labels when Gemini is unavailable."""
    parts = []
    if objects:
        parts.append(f"This photo contains {', '.join(str(o) for o in objects[:5])}")
    if emotions:
        parts.append(f"The people appear {', '.join(str(e) for e in emotions[:3])}")
    return ". ".join(parts) + "." if parts else "A photo from your camera roll."


def generate_description(image_bytes: bytes, objects: list, emotions: list) -> str:
    """Generate a natural language description of an image using Gemini vision.
    Falls back to a label-based description if the API is unavailable or rate-limited."""
    if not settings.gemini_api_key:
        return _label_fallback_description(objects, emotions)

    prompt = f"""You are describing an image for a user.
Detected objects: {objects}
Detected emotions: {emotions}

Using the image and these tags, generate a natural, conversational description.
Keep it 1-3 sentences."""

    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            ],
        )
        return response.text.strip()
    except Exception as e:
        print(f"[gemini] generate_description fell back to labels: {e}")
        return _label_fallback_description(objects, emotions)
