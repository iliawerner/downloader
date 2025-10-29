"""Integration helpers for ``yt-dlp``."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

from yt_dlp import YoutubeDL


class YtDlpExtractor:
    """Thin wrapper around :class:`yt_dlp.YoutubeDL`."""

    def __init__(self, **options: Any) -> None:
        defaults: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            # Force Android client and Po token to avoid "confirm you're not a bot" blocks.
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                    "po_token": ["1"],
                }
            },
        }
        self._options: Dict[str, Any] = {**defaults, **_without(options, "extractor_args")}
        self._options["extractor_args"] = _merge_extractor_args(
            defaults.get("extractor_args", {}),
            options.get("extractor_args", {}),
        )

    def extract(self, url: str) -> Dict[str, Any]:
        """Fetch raw metadata for *url* using ``yt-dlp``."""

        with YoutubeDL(self._options) as ydl:
            return ydl.extract_info(url, download=False)


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
            if isinstance(value, list):
                existing = list(target.get(name, [])) if isinstance(target.get(name), list) else []
                for item in value:
                    if item not in existing:
                        existing.append(item)
                target[name] = existing
            else:
                target[name] = value

    youtube_args = merged.setdefault("youtube", {})
    _ensure_list_value(youtube_args, "player_client", required_value="android")
    _ensure_list_value(youtube_args, "po_token", required_value="1")

    return merged


def _clone_value(value: Any) -> Any:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return {key: _clone_value(val) for key, val in value.items()}
    return value


def _ensure_list_value(args: Dict[str, Any], key: str, *, required_value: str) -> None:
    existing = args.get(key)
    if not isinstance(existing, list):
        args[key] = [required_value]
        return

    if required_value not in existing:
        existing.insert(0, required_value)
