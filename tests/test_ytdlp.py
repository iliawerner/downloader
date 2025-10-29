from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from downloader.core.ytdlp import YtDlpExtractor


class DummyYoutubeDL:
    def __init__(self, params):
        self.params = params
        self.recorded_url = None
        self.recorded_download = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download):
        self.recorded_url = url
        self.recorded_download = download
        return {"id": "dummy"}


def test_extractor_sets_expected_player_clients(monkeypatch):
    captured = {}

    def fake_youtubedl(options):
        captured["options"] = options
        return DummyYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    extractor = YtDlpExtractor()
    result = extractor.extract("https://example.com/video")

    assert result == {"id": "dummy"}
    extractor_args = captured["options"]["extractor_args"]
    youtube_args = extractor_args["youtube"]
    tab_args = extractor_args["youtubetab"]

    assert youtube_args["player_client"] == ["android", "mweb", "tv"]
    assert tab_args["player_client"] == youtube_args["player_client"]


def test_extractor_requests_best_format_selector(monkeypatch):
    captured = {}

    def fake_youtubedl(options):
        captured["options"] = options
        return DummyYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    extractor = YtDlpExtractor()
    extractor.extract("https://example.com/no-format")

    assert captured["options"].get("format") == "bestvideo*+bestaudio/best"
    assert "listformats" not in captured["options"]


def test_extractor_does_not_request_specific_format(monkeypatch):
    captured = {}

    def fake_youtubedl(options):
        captured["options"] = options
        return DummyYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    extractor = YtDlpExtractor(format="bestvideo*+bestaudio/best")
    extractor.extract("https://example.com/no-format")

    assert "format" not in captured["options"]


def test_extract_uses_no_download(monkeypatch):
    dummy = DummyYoutubeDL({})

    def fake_youtubedl(options):
        dummy.params = options
        return dummy

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    extractor = YtDlpExtractor()
    extractor.extract("https://example.com/another")

    assert dummy.recorded_download is False
    assert dummy.recorded_url == "https://example.com/another"


def test_extractor_uses_inline_cookies(monkeypatch):
    captured = {}

    class CookieAwareYoutubeDL(DummyYoutubeDL):
        def extract_info(self, url, download):
            cookiefile = self.params.get("cookiefile")
            captured["cookiefile"] = cookiefile
            if cookiefile:
                path = Path(cookiefile)
                captured["cookie_exists_during_call"] = path.is_file()
                captured["cookie_content"] = path.read_text(encoding="utf-8")
            return super().extract_info(url, download)

    def fake_youtubedl(options):
        captured["options"] = options
        return CookieAwareYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    extractor = YtDlpExtractor()
    cookies = "# Netscape HTTP Cookie File\nfoo\tbar\n"
    extractor.extract("https://example.com/inline-cookies", cookies=cookies)

    cookiefile = captured.get("cookiefile")
    assert cookiefile is not None
    assert captured["cookie_exists_during_call"] is True
    assert captured["cookie_content"] == cookies
    assert not Path(cookiefile).exists()
