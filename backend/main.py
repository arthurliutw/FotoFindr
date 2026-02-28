from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import init_db
from routes.profiles import router as profiles_router
from routes.search import router as search_router
from routes.upload import router as upload_router

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="FotoFindr API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
