"""Integration helpers for ``yt-dlp``."""

from __future__ import annotations

from typing import Any, Dict

from yt_dlp import YoutubeDL


class YtDlpExtractor:
    """Thin wrapper around :class:`yt_dlp.YoutubeDL`."""

    def __init__(self, **options: Any) -> None:
        defaults: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            # Force Android client to avoid "confirm you're not a bot" blocks.
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        }
        self._options: Dict[str, Any] = {**defaults, **options}

    def extract(self, url: str) -> Dict[str, Any]:
        """Fetch raw metadata for *url* using ``yt-dlp``."""

        with YoutubeDL(self._options) as ydl:
            return ydl.extract_info(url, download=False)
