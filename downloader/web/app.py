"""Application factory for the FastAPI interface."""

from __future__ import annotations

from fastapi import FastAPI

from ..services import MediaService
from .routes import create_router


def create_app(service: MediaService | None = None) -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    service = service or MediaService()
    app = FastAPI(title="YouTube Stream Inspector", version="2.0.0")
    app.include_router(create_router(service))
    return app
