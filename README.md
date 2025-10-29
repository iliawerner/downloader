# downloader

Утилита командной строки для получения прямых ссылок на загрузку аудио и видео потоков с платформ, поддерживаемых [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Использование

```bash
python -m downloader <youtube-url>
```

Пример вывода:

```
Title: Sample Video
Source: https://www.youtube.com/watch?v=...

Video streams:
  - format=137, type=video/mp4, resolution=1920x1080, bitrate=4500kbps, fps=30, size=50.2MB
    url: https://...
  - ...

Audio streams:
  - format=140, type=audio/m4a, bitrate=128kbps, size=5.3MB
    url: https://...
```

Для получения структурированных данных в JSON-формате:

```bash
python -m downloader <youtube-url> --json
```

> **Внимание.** Соблюдайте условия использования платформы-источника и действующего законодательства. Полученные ссылки предназначены исключительно для научных и обучающих целей.
