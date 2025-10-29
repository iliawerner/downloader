# downloader

Утилита с интерфейсами командной строки и веб-приложения для получения прямых ссылок на загрузку аудио и видео потоков с платформ, поддерживаемых [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Использование CLI

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

## Веб-интерфейс

Локальный запуск FastAPI-приложения:

```bash
uvicorn downloader.web:app --reload
```

После запуска откройте [http://127.0.0.1:8000](http://127.0.0.1:8000) и вставьте ссылку на интересующее видео. Сервер предоставляет HTML-страницу и JSON-API по адресу `/api/streams?url=...`.

### Деплой на Vercel

В репозитории присутствует директория `api/` с точкой входа `index.py`, поэтому достаточно выполнить стандартную публикацию Python-приложения на Vercel:

```bash
vercel deploy --prod
```

Vercel автоматически установит зависимости из `requirements.txt` и поднимет FastAPI-приложение.

> **Внимание.** Соблюдайте условия использования платформы-источника и действующего законодательства. Полученные ссылки предназначены исключительно для научных и обучающих целей.
