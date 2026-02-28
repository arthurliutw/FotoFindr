"""
Database helpers — Snowflake for metadata, numpy for vector similarity search.
"""

import json
import uuid
from typing import Optional

import numpy as np
import snowflake.connector
from snowflake.connector import DictCursor

from config import settings


def _require_snowflake_settings() -> None:
    required = {
        "SNOWFLAKE_ACCOUNT": settings.snowflake_account,
        "SNOWFLAKE_USER": settings.snowflake_user,
        "SNOWFLAKE_PASSWORD": settings.snowflake_password,
        "SNOWFLAKE_DATABASE": settings.snowflake_database,
        "SNOWFLAKE_SCHEMA": settings.snowflake_schema,
        "SNOWFLAKE_WAREHOUSE": settings.snowflake_warehouse,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(f"Missing Snowflake settings: {', '.join(missing)}")


def _get_conn():
    _require_snowflake_settings()
    return snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=settings.snowflake_password,
        database=settings.snowflake_database,
        schema=settings.snowflake_schema,
        warehouse=settings.snowflake_warehouse,
        role=settings.snowflake_role or None,
    )


def _normalize_row(row: dict) -> dict:
    return {k.lower(): v for k, v in row.items()}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS photos (
        id STRING PRIMARY KEY,
        user_id STRING NOT NULL,
        storage_url STRING NOT NULL,
        status STRING DEFAULT 'uploaded',
        modal_call_id STRING,
        error_message STRING,
        status_updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        caption STRING,
        tags STRING DEFAULT '[]',
        detected_objects STRING DEFAULT '[]',
        emotions STRING DEFAULT '[]',
        person_ids STRING DEFAULT '[]',
        importance_score FLOAT DEFAULT 1.0,
        low_value_flags STRING DEFAULT '[]',
        embedding STRING,
        created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS people (
        id STRING PRIMARY KEY,
        user_id STRING NOT NULL,
        name STRING,
        embedding_centroid STRING,
        photo_count INTEGER DEFAULT 0,
        cover_photo_url STRING,
        created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """,
    "ALTER TABLE photos ADD COLUMN IF NOT EXISTS status STRING DEFAULT 'uploaded'",
    "ALTER TABLE photos ADD COLUMN IF NOT EXISTS modal_call_id STRING",
    "ALTER TABLE photos ADD COLUMN IF NOT EXISTS error_message STRING",
    "ALTER TABLE photos ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()",
]


def init_db() -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            for stmt in SCHEMA_SQL:
                cur.execute(stmt)


def insert_photo(
    photo_id: str,
    user_id: str,
    storage_url: str,
    status: str = "uploaded",
    modal_call_id: str | None = None,
) -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO photos (id, user_id, storage_url, status, modal_call_id, status_updated_at)
                SELECT %s, %s, %s, %s, %s, CURRENT_TIMESTAMP()
                WHERE NOT EXISTS (SELECT 1 FROM photos WHERE id = %s)
                """,
                (photo_id, user_id, storage_url, status, modal_call_id, photo_id),
            )


def update_photo_status(
    photo_id: str,
    status: str,
    *,
    modal_call_id: str | None = None,
    error_message: str | None = None,
) -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE photos
                SET status = %s,
                    modal_call_id = COALESCE(%s, modal_call_id),
                    error_message = %s,
                    status_updated_at = CURRENT_TIMESTAMP()
                WHERE id = %s
                """,
                (status, modal_call_id, error_message, photo_id),
            )


def get_photo_status(photo_id: str) -> dict | None:
    with _get_conn() as conn:
        with conn.cursor(DictCursor) as cur:
            cur.execute(
                """
                SELECT id, user_id, status, modal_call_id, error_message, status_updated_at
                FROM photos
                WHERE id = %s
                """,
                (photo_id,),
            )
            row = cur.fetchone()
    return _normalize_row(row) if row else None


def update_photo_pipeline_result(photo_id: str, result: dict) -> None:
    embedding = result.get("embedding")
    embedding_json = json.dumps(embedding) if embedding else None

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE photos SET
                    caption = %s,
                    tags = %s,
                    detected_objects = %s,
                    emotions = %s,
                    person_ids = %s,
                    importance_score = %s,
                    low_value_flags = %s,
                    embedding = %s,
                    status = 'completed',
                    error_message = NULL,
                    status_updated_at = CURRENT_TIMESTAMP()
                WHERE id = %s
                """,
                (
                    result.get("caption"),
                    json.dumps(result.get("tags", [])),
                    result.get("detected_objects", "[]"),
                    result.get("emotions", "[]"),
                    json.dumps(result.get("person_ids", [])),
                    result.get("importance_score", 1.0),
                    json.dumps(result.get("low_value_flags", [])),
                    embedding_json,
                    photo_id,
                ),
            )


def _row_to_dict(row: dict) -> dict:
    d = _normalize_row(row)
    for key in ("tags", "detected_objects", "emotions", "person_ids", "low_value_flags"):
        if isinstance(d.get(key), str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                d[key] = []
    d.pop("embedding", None)
    return d


def search_photos_by_vector(
    embedding: list[float],
    user_id: str,
    filters: Optional[dict] = None,
    limit: int = 20,
) -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(DictCursor) as cur:
            cur.execute(
                "SELECT * FROM photos WHERE user_id = %s AND embedding IS NOT NULL",
                (user_id,),
            )
            rows = cur.fetchall()

    scored = []
    for row in rows:
        d = _normalize_row(row)
        try:
            row_emb = json.loads(d["embedding"])
        except (json.JSONDecodeError, TypeError):
            continue

        if filters:
            if filters.get("emotion"):
                emotions_raw = d.get("emotions", "[]")
                emotions = json.loads(emotions_raw) if isinstance(emotions_raw, str) else emotions_raw
                dominant_emotions = [e.get("dominant", "") for e in emotions if isinstance(e, dict)]
                if filters["emotion"].lower() not in [e.lower() for e in dominant_emotions]:
                    continue
            if filters.get("exclude_low_value"):
                score = d.get("importance_score", 1.0) or 1.0
                if score < 0.4:
                    continue

        sim = _cosine_similarity(embedding, row_emb)
        d["similarity"] = sim
        scored.append(d)

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return [_row_to_dict(d) for d in scored[:limit]]


def get_all_photos_for_user(user_id: str) -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(DictCursor) as cur:
            cur.execute(
                "SELECT * FROM photos WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
    return [_row_to_dict(row) for row in rows]


def get_or_create_person(
    user_id: str, embedding: list[float], threshold: float = 0.75
) -> str:
    with _get_conn() as conn:
        with conn.cursor(DictCursor) as cur:
            cur.execute(
                """
                SELECT id, embedding_centroid
                FROM people
                WHERE user_id = %s AND embedding_centroid IS NOT NULL
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    best_id = None
    best_sim = 0.0
    for row in rows:
        row = _normalize_row(row)
        try:
            centroid = json.loads(row["embedding_centroid"])
        except (json.JSONDecodeError, TypeError):
            continue
        sim = _cosine_similarity(embedding, centroid)
        if sim > best_sim:
            best_sim = sim
            best_id = str(row["id"])

    if best_sim >= threshold and best_id:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE people SET photo_count = photo_count + 1 WHERE id = %s",
                    (best_id,),
                )
        return best_id

    person_id = str(uuid.uuid4())
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO people (id, user_id, embedding_centroid, photo_count) VALUES (%s, %s, %s, 1)",
                (person_id, user_id, json.dumps(embedding)),
            )
    return person_id


def name_person(person_id: str, name: str) -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE people SET name = %s WHERE id = %s", (name, person_id))


def get_people(user_id: str) -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(DictCursor) as cur:
            cur.execute(
                """
                SELECT id, user_id, name, photo_count, cover_photo_url
                FROM people
                WHERE user_id = %s
                ORDER BY photo_count DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    return [_normalize_row(row) for row in rows]
