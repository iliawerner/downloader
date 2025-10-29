# downloader/core/ytdlp.py

"""Integration helpers for ``yt-dlp``."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict

from yt_dlp import YoutubeDL


class YtDlpExtractor:
    """Thin wrapper around :class:`yt_dlp.YoutubeDL`."""

    def __init__(self) -> None:
        """Initializes the extractor with default options."""
        self._options: Dict[str, Any] = _build_default_options()

    def extract(self, url: str, cookies: str | None = None) -> Dict[str, Any]:
        """Fetch raw metadata for *url* using ``yt-dlp``."""
        options = self._options.copy()
        cookie_path: str | None = None

        if cookies:
            # When cookies are passed dynamically, create a temporary file.
            # This is the primary method for Vercel.
            temp_file = NamedTemporaryFile("w+", delete=False, encoding="utf-8")
            try:
                temp_file.write(cookies)
                temp_file.flush()
            finally:
                temp_file.close()

            cookie_path = temp_file.name
            options["cookiefile"] = cookie_path
            # Ensure dynamic cookies override any other cookie settings.
            options.pop("cookiesfrombrowser", None)

        try:
            with YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as exc:
            # --- НАЧАЛО ИЗМЕНЕНИЙ ---
            # Если возникает любая ошибка, добавляем к ней отладочную информацию
            # о переданных опциях.
            debug_info = f"DEBUG_INFO: Options passed to yt-dlp: {options}"
            raise type(exc)(f"{str(exc)}\n\n{debug_info}") from exc
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        finally:
            if cookie_path:
                with suppress(OSError):
                    Path(cookie_path).unlink()


def _build_default_options() -> Dict[str, Any]:
    """Builds the base dictionary of options for yt-dlp."""

    # Use a variety of clients to mimic real devices, reducing the chance of blocks.
    player_clients = ["android", "mweb", "tv"]
    extractor_args: Dict[str, Dict[str, Any]] = {
        "youtube": {"player_client": player_clients},
        "youtubetab": {"player_client": player_clients},
    }

    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": extractor_args,
    }

    # Note: Environment-based cookie handling is removed from here
    # as dynamic cookies from the UI are now the primary method.
    return options
