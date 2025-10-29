"""Command line interface for listing downloadable media streams."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any, Dict, Optional, Sequence

from .streams import MediaInfo, StreamInfo, get_media_info


def _stream_to_dict(stream: StreamInfo) -> Dict[str, Any]:
    data = asdict(stream)
    if stream.filesize is not None:
        data["filesize_mb"] = round(stream.filesize / (1024 * 1024), 2)
    return data


def media_info_to_dict(info: MediaInfo) -> Dict[str, Any]:
    return {
        "title": info.title,
        "webpage_url": info.webpage_url,
        "video_streams": [_stream_to_dict(stream) for stream in info.video_streams],
        "audio_streams": [_stream_to_dict(stream) for stream in info.audio_streams],
    }


def print_media_info(info: MediaInfo) -> None:
    print(f"Title: {info.title}")
    print(f"Source: {info.webpage_url}\n")

    if not info.video_streams:
        print("No downloadable video streams found.")
    else:
        print("Video streams:")
        for stream in info.video_streams:
            details = [
                f"format={stream.format_id}",
                f"type={stream.mime_type}",
                f"resolution={stream.resolution}",
                f"bitrate={stream.bitrate}",
            ]
            if stream.fps:
                details.append(f"fps={stream.fps}")
            if stream.filesize:
                details.append(f"size={round(stream.filesize / (1024 * 1024), 2)}MB")
            details_str = ", ".join(details)
            print(f"  - {details_str}")
            print(f"    url: {stream.url}")

    print()
    if not info.audio_streams:
        print("No dedicated audio streams found.")
    else:
        print("Audio streams:")
        for stream in info.audio_streams:
            details = [
                f"format={stream.format_id}",
                f"type={stream.mime_type}",
                f"bitrate={stream.bitrate}",
            ]
            if stream.filesize:
                details.append(f"size={round(stream.filesize / (1024 * 1024), 2)}MB")
            details_str = ", ".join(details)
            print(f"  - {details_str}")
            print(f"    url: {stream.url}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List downloadable video and audio streams for a media URL.",
    )
    parser.add_argument("url", help="Media URL (e.g. a YouTube video).")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of formatted text.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    info = get_media_info(args.url)

    if args.json:
        print(json.dumps(media_info_to_dict(info), ensure_ascii=False, indent=2))
    else:
        print_media_info(info)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
