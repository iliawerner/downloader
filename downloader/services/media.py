"""High-level API for inspecting downloadable media streams."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Protocol

from ..core import MediaResult, MediaStream, YtDlpExtractor


class MediaExtractor(Protocol):
    """Protocol describing extractor implementations."""

    def extract(self, url: str) -> Dict[str, Any]:
        ...


class MediaService:
    """Facade that transforms raw ``yt-dlp`` data into structured objects."""

    def __init__(self, extractor: MediaExtractor | None = None) -> None:
        self._extractor: MediaExtractor = extractor or YtDlpExtractor()

    def get_media(self, url: str) -> MediaResult:
        """Retrieve structured metadata for *url*."""

        payload = self._extractor.extract(url)
        formats = payload.get("formats") or []

        video_streams = list(self._build_streams(formats, kind="video"))
        audio_streams = list(self._build_streams(formats, kind="audio"))

        title = payload.get("title") or ""
        page_url = payload.get("webpage_url") or url

        return MediaResult(
            title=title,
            page_url=page_url,
            video_streams=video_streams,
            audio_streams=audio_streams,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_streams(self, formats: Iterable[Dict[str, Any]], *, kind: str) -> Iterable[MediaStream]:
        for fmt in formats:
            stream = self._convert_format(fmt, kind=kind)
            if stream:
                yield stream

    def _convert_format(self, fmt: Dict[str, Any], *, kind: str) -> MediaStream | None:
        if "url" not in fmt:
            return None

        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")

        if kind == "video":
            if not vcodec or vcodec == "none":
                return None
        elif kind == "audio":
            if not acodec or acodec == "none":
                return None
            if vcodec and vcodec != "none":
                # Skip progressive formats in the dedicated audio list.
                return None
        else:  # pragma: no cover - defensive guard
            raise ValueError(f"Unsupported kind: {kind}")

        format_id = str(fmt.get("format_id") or fmt.get("format") or "unknown")
        mime_type = self._build_mime_type(fmt, kind=kind)
        resolution = self._build_resolution(fmt, kind=kind)
        bitrate = self._build_bitrate(fmt)
        fps = self._build_fps(fmt)
        filesize = self._build_filesize(fmt)
        url = fmt["url"]

        extra: Dict[str, Any] = {}
        if fmt.get("format_note"):
            extra["note"] = str(fmt["format_note"])
        if fmt.get("dynamic_range"):
            extra["dynamic_range"] = str(fmt["dynamic_range"])

        return MediaStream(
            format_id=format_id,
            mime_type=mime_type,
            resolution=resolution,
            bitrate_kbps=bitrate,
            fps=fps,
            filesize_bytes=filesize,
            url=url,
            extra=extra,
        )

    @staticmethod
    def _build_mime_type(fmt: Dict[str, Any], *, kind: str) -> str:
        ext = (fmt.get("ext") or "bin").lower()
        if kind == "video":
            return f"video/{ext}"
        return f"audio/{ext}"

    @staticmethod
    def _build_resolution(fmt: Dict[str, Any], *, kind: str) -> str | None:
        if kind != "video":
            return None
        width = fmt.get("width")
        height = fmt.get("height")
        if width and height:
            return f"{width}x{height}"
        resolution = fmt.get("resolution") or fmt.get("format_note")
        if resolution:
            return str(resolution)
        return None

    @staticmethod
    def _build_bitrate(fmt: Dict[str, Any]) -> int | None:
        for key in ("tbr", "vbr", "abr"):
            value = fmt.get(key)
            if isinstance(value, (int, float)):
                return int(value)
        return None

    @staticmethod
    def _build_fps(fmt: Dict[str, Any]) -> int | None:
        fps = fmt.get("fps")
        if isinstance(fps, (int, float)):
            return int(fps)
        return None

    @staticmethod
    def _build_filesize(fmt: Dict[str, Any]) -> int | None:
        size = fmt.get("filesize") or fmt.get("filesize_approx")
        if isinstance(size, (int, float)):
            return int(size)
        return None
