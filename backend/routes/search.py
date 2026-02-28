from fastapi import APIRouter
from models import SearchRequest, SearchResult, PhotoMetadata
from db import search_photos_by_vector, get_all_photos_for_user
from search.embed import embed_text
from search.query import parse_filters
from search.narration import generate_narration

router = APIRouter()


@router.post("/", response_model=SearchResult)
async def search_photos(req: SearchRequest):
    embedding = await embed_text(req.query)
    filters = parse_filters(req.query)
    rows = search_photos_by_vector(
        embedding=embedding,
        user_id=str(req.user_id),
        filters=filters,
        limit=req.limit,
    )
    photos = [PhotoMetadata(**row) for row in rows]
    narration_text, narration_url = await generate_narration(req.query, photos)
    return SearchResult(
        photos=photos,
        narration=narration_url,
        narration_text=narration_text,
        total=len(photos),
    )
