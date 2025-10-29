"""Command-line interface for the media inspector."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .core import MediaStream
from .services import MediaService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect downloadable media streams.")
    parser.add_argument("url", help="Video URL supported by yt-dlp.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON instead of a human-readable table.",
    )
    return parser


def format_size(size: int | None) -> str:
    if not size:
        return "unknown"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} {units[-1]}"


def describe_streams(kind: str, streams: Iterable[MediaStream]) -> str:
    lines = [f"{kind} streams:"]
    if not streams:
        lines.append("  (none)")
        return "\n".join(lines)
    for stream in streams:
        bitrate = f"{stream.bitrate_kbps}kbps" if stream.bitrate_kbps else "unknown"
        fps = f", fps={stream.fps}" if stream.fps else ""
        resolution = f", resolution={stream.resolution}" if stream.resolution else ""
        size = format_size(stream.filesize_bytes)
        lines.append(
            f"  - format={stream.format_id}, type={stream.mime_type}{resolution}, bitrate={bitrate}{fps}, size={size}"
        )
        lines.append(f"    url: {stream.url}")
        if stream.extra:
            for key, value in stream.extra.items():
                lines.append(f"    {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    service = MediaService()
    try:
        result = service.get_media(args.url)
    except Exception as exc:  # pragma: no cover - propagate extractor errors
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(f"Title: {result.title or 'Untitled'}")
    print(f"Source: {result.page_url}")
    print()
    print(describe_streams("Video", result.video_streams))
    print()
    print(describe_streams("Audio", result.audio_streams))
    return 0
