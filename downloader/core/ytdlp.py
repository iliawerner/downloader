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

        sanitized_options = _sanitize_options(options, cookie_path=cookie_path)

        try:
            with YoutubeDL(options) as ydl:
                # ``process=True`` (the default) is required so yt-dlp performs the
                # full extraction pipeline which populates the ``formats`` list with
                # direct stream URLs. Skipping the processing step yields minimal
                # metadata without usable download links, which results in empty
                # stream tables on the frontend.
                info = ydl.extract_info(url, download=False)
                info.setdefault(
                    "_stream_inspector",
                    {},
                ).update(
                    {
                        "yt_dlp_options": sanitized_options,
                        "raw_format_count": len(info.get("formats") or []),
                    }
                )
                return info
        except Exception as exc:
            # --- НАЧАЛО ИЗМЕНЕНИЙ ---
            # Если возникает любая ошибка, добавляем к ней отладочную информацию
            # о переданных опциях.
            debug_info = f"DEBUG_INFO: Options passed to yt-dlp: {sanitized_options}"
            raise type(exc)(f"{str(exc)}\n\n{debug_info}") from exc
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        finally:
            if cookie_path:
                with suppress(OSError):
                    Path(cookie_path).unlink()


def _build_default_options() -> Dict[str, Any]:
    """Builds the base dictionary of options for yt-dlp."""

    # Use a variety of clients to mimic real devices, reducing the chance of blocks.
    # The "web" client must be included so yt-dlp can retrieve the JavaScript
    # player needed to decipher signature ciphers and expose direct stream URLs.
    # Without it, some videos only return metadata without populated ``formats``.
    player_clients = ["web", "android", "mweb", "tv"]
    extractor_args: Dict[str, Dict[str, Any]] = {
        "youtube": {"player_client": player_clients},
        "youtubetab": {"player_client": player_clients},
    }

    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # ``ignoreconfig`` disables reading the user's yt-dlp configuration
        # files.  When third-party configs provide values such as ``format`` or
        # ``outtmpl`` they can constrain the available streams or cause empty
        # results in metadata mode.  Explicitly opting out keeps the extractor
        # deterministic regardless of the deployment environment.
        "ignoreconfig": True,
        # Некоторые видео (например, требующие авторизации или с возрастными
        # ограничениями) могут не иметь форматов, удовлетворяющих выборке
        # ``bestvideo+bestaudio/best`` по умолчанию. В таком случае yt-dlp
        # генерирует ``Requested format is not available`` и останавливает
        # обработку, хотя список ``formats`` уже получен. ``ignore_no_formats_error``
        # позволяет продолжить выполнение и вернуть метаданные, даже если
        # ни один формат не выбран для скачивания.
        "ignore_no_formats_error": True,
        # Serverless providers such as Vercel frequently disallow outgoing HEAD requests or strip cookies from them. yt-dlp validates every format by issuing HEAD probes when ``check_formats`` is enabled which causes the extractor to discard otherwise valid stream URLs. Disabling the check preserves the raw ``formats`` data so the UI can still present options.
        "check_formats": False,
        # ``extract_info`` без ``process`` возвращает метаданные для *всех* потоков.
        # Чтобы не ограничивать выдачу и не скрыть доступные потоки, формат не
        # задаётся явно. Это гарантирует, что интерфейс увидит полный список
        # вариантов и не отобразит «No streams available».
        "extractor_args": extractor_args,
    }

    # Note: Environment-based cookie handling is removed from here
    # as dynamic cookies from the UI are now the primary method.
    return options


def _sanitize_options(options: Dict[str, Any], *, cookie_path: str | None) -> Dict[str, Any]:
    """Create a sanitized copy of *options* suitable for logging."""

    sanitized: Dict[str, Any] = {}
    for key, value in options.items():
        if key == "cookiefile" and cookie_path:
            sanitized[key] = "<temporary file>"
            continue
        if isinstance(value, set):
            sanitized[key] = sorted(value)
            continue
        sanitized[key] = value
    return sanitized
