"""HTTP routes for the FastAPI application."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from ..services import MediaService
from .schemas import MediaLookupRequest, MediaSchema
from .templates import INDEX_HTML


class Dependencies:
    """Container for dependency callables."""

    def __init__(self, service: MediaService) -> None:
        self._service = service

    def get_service(self) -> MediaService:
        return self._service


def create_router(service: MediaService) -> APIRouter:
    deps = Dependencies(service)
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(INDEX_HTML)

    @router.post("/api/streams", response_model=MediaSchema)
    async def list_streams(
        request: MediaLookupRequest,
        media_service: MediaService = Depends(deps.get_service),
    ) -> MediaSchema:
        loop = asyncio.get_running_loop()
        cookies = None
        if request.cookies is not None:
            stripped = request.cookies.strip()
            cookies = stripped or None
        try:
            result = await loop.run_in_executor(
                None,
                media_service.get_media,
                str(request.url),
                cookies,
            )
        except Exception as exc:  # pragma: no cover - propagate extractor errors
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return MediaSchema.model_validate(result)

    return router
