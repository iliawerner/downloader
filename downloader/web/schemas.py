"""Pydantic response schemas for the HTTP API."""

from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel, ConfigDict


class StreamSchema(BaseModel):
    format_id: str
    mime_type: str
    resolution: str | None = None
    bitrate_kbps: int | None = None
    fps: int | None = None
    filesize_bytes: int | None = None
    url: AnyHttpUrl
    extra: dict[str, str] | None = None

    model_config = ConfigDict(from_attributes=True)


class MediaSchema(BaseModel):
    title: str
    page_url: AnyHttpUrl
    video_streams: list[StreamSchema]
    audio_streams: list[StreamSchema]

    model_config = ConfigDict(from_attributes=True)
