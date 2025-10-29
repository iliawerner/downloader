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


def test_extractor_forces_android_client(monkeypatch):
    captured = {}

    def fake_youtubedl(options):
        captured["options"] = options
        return DummyYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    extractor = YtDlpExtractor()
    result = extractor.extract("https://example.com/video")

    assert result == {"id": "dummy"}
    assert captured["options"]["extractor_args"]["youtube"]["player_client"] == ["android"]


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
