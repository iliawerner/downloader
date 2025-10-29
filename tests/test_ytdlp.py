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
    monkeypatch.delenv("YT_DLP_PO_TOKEN", raising=False)
    monkeypatch.delenv("YT_DLP_PO_TOKENS", raising=False)
    monkeypatch.delenv("YT_DLP_PO_TOKEN_FILE", raising=False)
    monkeypatch.delenv("YT_DLP_PLAYER_CLIENTS", raising=False)
    monkeypatch.delenv("YT_DLP_PLAYER_CLIENT", raising=False)
    monkeypatch.delenv("YT_DLP_VISITOR_DATA", raising=False)

    extractor = YtDlpExtractor()
    result = extractor.extract("https://example.com/video")

    assert result == {"id": "dummy"}
    youtube_args = captured["options"]["extractor_args"]["youtube"]
    assert youtube_args["player_client"] == ["android"]
    assert "po_token" not in youtube_args


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


def test_extractor_preserves_custom_args(monkeypatch):
    captured = {}

    def fake_youtubedl(options):
        captured["options"] = options
        return DummyYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)
    monkeypatch.delenv("YT_DLP_PO_TOKEN", raising=False)
    monkeypatch.delenv("YT_DLP_PO_TOKENS", raising=False)
    monkeypatch.delenv("YT_DLP_PO_TOKEN_FILE", raising=False)
    monkeypatch.delenv("YT_DLP_PLAYER_CLIENTS", raising=False)
    monkeypatch.delenv("YT_DLP_PLAYER_CLIENT", raising=False)
    monkeypatch.delenv("YT_DLP_VISITOR_DATA", raising=False)

    extractor = YtDlpExtractor(
        extractor_args={
            "youtube": {
                "player_client": ["ios"],
                "custom_flag": ["value"],
            },
            "vimeo": {"foo": ["bar"]},
        }
    )

    extractor.extract("https://example.com/merged")

    youtube_args = captured["options"]["extractor_args"]["youtube"]
    assert youtube_args["player_client"] == ["android", "ios"]
    assert youtube_args["custom_flag"] == ["value"]

    assert captured["options"]["extractor_args"]["vimeo"] == {"foo": ["bar"]}


def test_extractor_uses_env_tokens(monkeypatch, tmp_path):
    captured = {}

    def fake_youtubedl(options):
        captured["options"] = options
        return DummyYoutubeDL(options)

    monkeypatch.setattr("downloader.core.ytdlp.YoutubeDL", fake_youtubedl)

    token_file = tmp_path / "tokens.txt"
    token_file.write_text("file-token-1\nfile-token-2\n", encoding="utf-8")

    monkeypatch.setenv("YT_DLP_PO_TOKEN", "env-token")
    monkeypatch.setenv("YT_DLP_PO_TOKEN_FILE", str(token_file))
    monkeypatch.delenv("YT_DLP_PLAYER_CLIENTS", raising=False)
    monkeypatch.delenv("YT_DLP_PLAYER_CLIENT", raising=False)

    extractor = YtDlpExtractor()
    extractor.extract("https://example.com/with-token")

    youtube_args = captured["options"]["extractor_args"]["youtube"]
    assert youtube_args["player_client"] == ["mweb", "android"]
    assert youtube_args["po_token"] == ["env-token", "file-token-1", "file-token-2"]
