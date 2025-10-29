"""Vercel entrypoint exposing the FastAPI app."""

from downloader.web import app

__all__ = ["app"]
