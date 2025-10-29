# downloader/core/ytdlp.py

"""Integration helpers for ``yt-dlp``."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Tuple
import os
import re

from yt_dlp import YoutubeDL
from yt_dlp.cookies import SUPPORTED_BROWSERS, SUPPORTED_KEYRINGS


class YtDlpExtractor:
    """Thin wrapper around :class:`yt_dlp.YoutubeDL`."""

    def __init__(self, **options: Any) -> None:
        defaults: Dict[str, Any] = _build_default_options()
        self._options: Dict[str, Any] = {**defaults, **_without(options, "extractor_args")}
        self._options["extractor_args"] = _merge_extractor_args(
            defaults.get("extractor_args", {}),
            options.get("extractor_args", {}),
        )

    def extract(self, url: str, cookies: str | None = None) -> Dict[str, Any]:
        """Fetch raw metadata for *url* using ``yt-dlp``."""

        options = dict(self._options)
        cookie_path: str | None = None

        if cookies:
            options.pop("cookiesfrombrowser", None)
            options.pop("cookiefile", None)

            temp_file = NamedTemporaryFile("w+", delete=False, encoding="utf-8")
            try:
                temp_file.write(cookies)
                temp_file.flush()
            finally:
                temp_file.close()

            cookie_path = temp_file.name
            options["cookiefile"] = cookie_path

        try:
            with YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)
        finally:
            if cookie_path:
                with suppress(OSError):
                    Path(cookie_path).unlink()


def _without(mapping: Mapping[str, Any], *keys: str) -> Dict[str, Any]:
    return {key: value for key, value in mapping.items() if key not in keys}


def _merge_extractor_args(
    defaults: Dict[str, Dict[str, Any]],
    overrides: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {
        extractor: {name: _clone_value(value) for name, value in args.items()}
        for extractor, args in defaults.items()
    }

    for extractor, args in overrides.items():
        target = merged.setdefault(extractor, {})
        for name, value in args.items():
            target[name] = value

    return merged


def _clone_value(value: Any) -> Any:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return {key: _clone_value(val) for key, val in value.items()}
    return value

def _build_default_options() -> Dict[str, Any]:
    youtube_args: Dict[str, Any] = {}

    player_clients = ["android_sdkless", "android", "android_vr", "ios", "tv", "mweb"]
    youtube_args["player_client"] = player_clients
    
    extractor_args: Dict[str, Dict[str, Any]] = {
        "youtube": _clone_value(youtube_args),
        "youtubetab": _clone_value(youtube_args),
    }

    # CRITICAL: Do NOT add a "format" key here. 
    # The application is designed to list all available formats, not select one.
    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": extractor_args,
    }

    options.update(_cookies_options_from_env())

    return options

def _cookies_options_from_env() -> Dict[str, Any]:
    """
    Builds cookie options, prioritizing Vercel's environment variable method.
    """
    options: Dict[str, Any] = {}
    
    cookie_content = os.getenv("YT_DLP_COOKIES_CONTENT")
    if cookie_content:
        # Vercel provides a writable /tmp directory. This is the primary method.
        tmp_cookie_path = "/tmp/cookies.txt"
        try:
            with open(tmp_cookie_path, "w", encoding="utf-8") as f:
                f.write(cookie_content)
            options["cookiefile"] = tmp_cookie_path
            # If this method succeeds, return immediately. Do not process other methods.
            return options
        except OSError:
            # If writing to /tmp fails, we'll fall through to other methods.
            pass

    # Fallback method 1: Read from a file path specified in an env var.
    # Useful for local development, but not for Vercel's read-only filesystem.
    cookiefile_path = os.getenv("YT_DLP_COOKIES_FILE")
    if cookiefile_path:
        path = Path(cookiefile_path).expanduser()
        if path.is_file():
            options["cookiefile"] = str(path)
            return options
            
    # Fallback method 2: Use cookies directly from a local browser.
    # Only for local development, will fail on Vercel.
    browser_spec = os.getenv("YT_DLP_COOKIES_FROM_BROWSER")
    if browser_spec:
        # This part of the original code for parsing browser spec is complex
        # and not needed for the Vercel target. We simplify to a direct pass.
        options["cookiesfrombrowser"] = tuple(part.strip() for part in browser_spec.split(':'))
        return options

    return options
