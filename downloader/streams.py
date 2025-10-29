"""Helpers for retrieving downloadable streams from supported platforms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from yt_dlp import YoutubeDL


@dataclass
class StreamInfo:
    """Information about a single downloadable stream."""

    format_id: str
    mime_type: str
    resolution: str
    bitrate: str
    fps: Optional[str]
    filesize: Optional[int]
    url: str

    @classmethod
    def from_format(cls, fmt: dict) -> "StreamInfo":
        height = fmt.get("height")
        width = fmt.get("width")
        fps = fmt.get("fps")
        if height and width:
            resolution = f"{width}x{height}"
        elif fmt.get("resolution"):
            resolution = str(fmt["resolution"])
        else:
            resolution = "unknown"

        tbr = fmt.get("tbr")
        abr = fmt.get("abr")
        if tbr:
            bitrate = f"{tbr}kbps"
        elif abr:
            bitrate = f"{abr}kbps"
        else:
            bitrate = "unknown"

        mime = fmt.get("ext") or "unknown"
        if fmt.get("acodec") != "none" and fmt.get("vcodec") != "none":
            mime_type = f"video/{mime} (muxed)"
        elif fmt.get("vcodec") != "none":
            mime_type = f"video/{mime}"
        else:
            mime_type = f"audio/{mime}"

        filesize = fmt.get("filesize") or fmt.get("filesize_approx")

        return cls(
            format_id=str(fmt.get("format_id", "unknown")),
            mime_type=mime_type,
            resolution=resolution,
            bitrate=bitrate,
            fps=str(int(fps)) if isinstance(fps, (int, float)) else None,
            filesize=int(filesize) if isinstance(filesize, (int, float)) else None,
            url=fmt["url"],
        )


@dataclass
class MediaInfo:
    """Collection of downloadable media streams."""

    title: str
    webpage_url: str
    video_streams: List[StreamInfo]
    audio_streams: List[StreamInfo]


def _filter_streams(formats: Iterable[dict], *, kind: str) -> List[StreamInfo]:
    filtered: List[StreamInfo] = []
    for fmt in formats:
        acodec = fmt.get("acodec")
        vcodec = fmt.get("vcodec")
        if kind == "video":
            if vcodec == "none":
                continue
        elif kind == "audio":
            if acodec == "none" or vcodec not in ("none", None):
                # Only include pure audio streams for the dedicated audio list.
                continue
        else:
            raise ValueError(f"Unsupported kind: {kind}")

        if "url" not in fmt:
            # Adaptive streams occasionally miss the direct URL when they require
            # additional manifest downloads. Skip those so that we only return
            # immediately downloadable links.
            continue

        filtered.append(StreamInfo.from_format(fmt))
    return filtered


def get_media_info(url: str) -> MediaInfo:
    """Fetch media streams for the given URL using ``yt-dlp``.

    Parameters
    ----------
    url:
        A video URL supported by ``yt-dlp`` (YouTube, etc.).

    Returns
    -------
    MediaInfo
        The structured data containing video and audio download links.
    """

    options = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats", [])
    video_streams = _filter_streams(formats, kind="video")
    audio_streams = _filter_streams(formats, kind="audio")

    return MediaInfo(
        title=info.get("title", ""),
        webpage_url=info.get("webpage_url", url),
        video_streams=video_streams,
        audio_streams=audio_streams,
    )
