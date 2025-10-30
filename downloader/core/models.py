"""Domain models describing downloadable media."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass(slots=True)
class MediaStream:
    """Description of a single downloadable media stream."""

    format_id: str
    mime_type: str
    resolution: Optional[str]
    bitrate_kbps: Optional[int]
    fps: Optional[int]
    filesize_bytes: Optional[int]
    url: str
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stream to a serializable dictionary."""

        payload: Dict[str, Any] = {
            "format_id": self.format_id,
            "mime_type": self.mime_type,
            "resolution": self.resolution,
            "bitrate_kbps": self.bitrate_kbps,
            "fps": self.fps,
            "filesize_bytes": self.filesize_bytes,
            "url": self.url,
        }
        if self.extra:
            payload["extra"] = self.extra
        return payload


@dataclass(slots=True)
class MediaResult:
    """Aggregated media metadata for a given source URL."""

    title: str
    page_url: str
    video_streams: List[MediaStream]
    audio_streams: List[MediaStream]
    debug: Dict[str, Any] | None = None

    def iter_streams(self) -> Iterable[MediaStream]:
        """Iterate over every stream regardless of media type."""

        yield from self.video_streams
        yield from self.audio_streams

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to primitive Python objects."""

        return {
            "title": self.title,
            "page_url": self.page_url,
            "video_streams": [stream.to_dict() for stream in self.video_streams],
            "audio_streams": [stream.to_dict() for stream in self.audio_streams],
            "debug": self.debug,
        }
