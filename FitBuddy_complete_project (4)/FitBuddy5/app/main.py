from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .database import init_db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered fitness plan generator using FastAPI, Jinja2, SQLite, "
        "and Google's Gemini models."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
