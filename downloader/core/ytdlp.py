"""Integration helpers for ``yt-dlp``."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, Iterable, List
import os

from yt_dlp import YoutubeDL


class YtDlpExtractor:
    """Thin wrapper around :class:`yt_dlp.YoutubeDL`."""

    def __init__(self, **options: Any) -> None:
        defaults: Dict[str, Any] = _build_default_options()
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

    return merged


def _clone_value(value: Any) -> Any:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return {key: _clone_value(val) for key, val in value.items()}
    return value

def _build_default_options() -> Dict[str, Any]:
    youtube_args: Dict[str, Any] = {}

    po_tokens = _po_tokens_from_env()
    player_clients = _player_clients_from_env(po_tokens)
    visitor_data = _visitor_data_from_env()

    if player_clients:
        youtube_args["player_client"] = player_clients
    if po_tokens:
        youtube_args["po_token"] = po_tokens
    if visitor_data:
        youtube_args["visitor_data"] = [visitor_data]

    extractor_args = {"youtube": youtube_args} if youtube_args else {}

    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": extractor_args,
    }


def _po_tokens_from_env() -> List[str]:
    tokens = _env_list("YT_DLP_PO_TOKEN", "YT_DLP_PO_TOKENS")

    file_tokens = _po_tokens_from_file(os.getenv("YT_DLP_PO_TOKEN_FILE"))
    if file_tokens:
        tokens.extend(file_tokens)

    return _unique(tokens)


def _po_tokens_from_file(path_str: str | None) -> List[str]:
    if not path_str:
        return []

    path = Path(path_str).expanduser()
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError:
        return []

    return [line.strip() for line in contents.splitlines() if line.strip()]


def _player_clients_from_env(po_tokens: Iterable[str]) -> List[str]:
    explicit = _env_list("YT_DLP_PLAYER_CLIENTS", "YT_DLP_PLAYER_CLIENT")
    if explicit:
        return _unique(explicit)

    clients = ["mweb", "android"] if list(po_tokens) else ["android"]
    return clients


def _visitor_data_from_env() -> str | None:
    visitor_data = os.getenv("YT_DLP_VISITOR_DATA")
    if visitor_data:
        visitor_data = visitor_data.strip()
    return visitor_data or None


def _env_list(*names: str) -> List[str]:
    values: List[str] = []
    for name in names:
        raw = os.getenv(name)
        if not raw:
            continue
        parts = raw.split(",")
        for part in parts:
            item = part.strip()
            if item:
                values.append(item)
    return values


def _unique(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
