"""
Text → vector embedding via Gemini text-embedding-004 (768-dim).
"""

import asyncio
from google import genai
from backend.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)


async def embed_text(text: str) -> list[float]:
    text = text.strip().replace("\n", " ")
    response = await asyncio.to_thread(
        _client.models.embed_content,
        model="models/text-embedding-004",
        contents=text,
    )
    return response.embeddings[0].values
