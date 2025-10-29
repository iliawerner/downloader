"""FastAPI application exposing stream metadata via HTTP."""

from __future__ import annotations

import asyncio
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .streams import MediaInfo, StreamInfo, get_media_info


app = FastAPI(title="Media Stream Downloader", version="1.0.0")


class StreamResponse(dict):
    """Dictionary helper that serializes :class:`StreamInfo`."""

    @classmethod
    def from_stream(cls, stream: StreamInfo) -> "StreamResponse":
        data = asdict(stream)
        return cls(data)


class MediaResponse(dict):
    """Dictionary helper that serializes :class:`MediaInfo`."""

    @classmethod
    def from_media_info(cls, info: MediaInfo) -> "MediaResponse":
        return cls(
            {
                "title": info.title,
                "webpage_url": info.webpage_url,
                "video_streams": [StreamResponse.from_stream(s) for s in info.video_streams],
                "audio_streams": [StreamResponse.from_stream(s) for s in info.audio_streams],
            }
        )


_INDEX_HTML = """
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Media Stream Downloader</title>
    <style>
      :root {
        color-scheme: light dark;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      }
      body {
        margin: 0;
        padding: 2rem 1rem 4rem;
        display: flex;
        justify-content: center;
      }
      main {
        width: min(960px, 100%);
      }
      h1 {
        font-size: 2rem;
        margin-bottom: 1rem;
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      }
      form {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
      }
      input[type=\"url\"] {
        flex: 1;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        border: 1px solid #8884;
        font-size: 1rem;
      }
      button {
        padding: 0.75rem 1.25rem;
        border-radius: 0.5rem;
        border: none;
        background: #2563eb;
        color: white;
        font-size: 1rem;
        cursor: pointer;
      }
      button:disabled {
        opacity: 0.6;
        cursor: progress;
      }
      .results {
        display: grid;
        gap: 1rem;
      }
      .card {
        border: 1px solid #8884;
        border-radius: 0.75rem;
        padding: 1rem;
      }
      .streams {
        overflow-x: auto;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th, td {
        padding: 0.5rem;
        border-bottom: 1px solid #8884;
        text-align: left;
        font-variant-numeric: tabular-nums;
      }
      th {
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
        opacity: 0.7;
      }
      caption {
        text-align: left;
        font-weight: 600;
        margin-bottom: 0.5rem;
      }
      .error {
        color: #dc2626;
        font-weight: 600;
      }
      footer {
        margin-top: 2rem;
        font-size: 0.85rem;
        opacity: 0.7;
      }
      a {
        color: inherit;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Media Stream Downloader</h1>
      <p>Paste a supported media URL to list direct download links for every available video and audio stream.</p>
      <form id=\"lookup-form\">
        <label class=\"sr-only\" for=\"url\">Media URL</label>
        <input id=\"url\" name=\"url\" type=\"url\" placeholder=\"https://www.youtube.com/watch?v=...\" required />
        <button type=\"submit\">Inspect</button>
      </form>
      <p id=\"status\"></p>
      <div class=\"results\" id=\"results\" hidden></div>
      <footer>
        Built with <code>yt-dlp</code>. This tool provides direct links without downloading the media.
      </footer>
    </main>
    <script>
      const form = document.getElementById('lookup-form');
      const urlInput = document.getElementById('url');
      const status = document.getElementById('status');
      const results = document.getElementById('results');
      const button = form.querySelector('button');

      function escapeHtml(str) {
        return str.replace(/[&<>\"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;','\'':'&#39;'}[c]));
      }

      function renderTable(title, streams) {
        if (!streams.length) {
          return `<div class=\"card\"><h2>${title}</h2><p>No streams available.</p></div>`;
        }
        const headers = ['Format', 'MIME Type', 'Resolution', 'Bitrate', 'FPS', 'Filesize', 'Download'];
        const rows = streams.map(stream => {
          const size = stream.filesize ? `${(stream.filesize / (1024 * 1024)).toFixed(2)} MiB` : '—';
          const fps = stream.fps || '—';
          return `<tr>
            <td>${escapeHtml(stream.format_id)}</td>
            <td>${escapeHtml(stream.mime_type)}</td>
            <td>${escapeHtml(stream.resolution)}</td>
            <td>${escapeHtml(stream.bitrate)}</td>
            <td>${fps}</td>
            <td>${size}</td>
            <td><a href=\"${stream.url}\" target=\"_blank\" rel=\"noopener noreferrer\">Download</a></td>
          </tr>`;
        }).join('');
        return `<div class=\"card streams\">
          <table>
            <caption>${title}</caption>
            <thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
      }

      async function lookup(url) {
        results.hidden = true;
        status.textContent = '';
        button.disabled = true;
        try {
          const response = await fetch(`/api/streams?url=${encodeURIComponent(url)}`);
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.detail || 'Request failed');
          }
          const cards = [];
          cards.push(`<div class=\"card\"><h2>${escapeHtml(payload.title || 'Untitled')}</h2>
            <p><a href=\"${payload.webpage_url}\" target=\"_blank\" rel=\"noopener noreferrer\">Open original page</a></p>
          </div>`);
          cards.push(renderTable('Video Streams', payload.video_streams));
          cards.push(renderTable('Audio Streams', payload.audio_streams));
          results.innerHTML = cards.join('');
          results.hidden = false;
        } catch (error) {
          status.innerHTML = `<span class=\"error\">${escapeHtml(error.message || 'Unexpected error')}</span>`;
        } finally {
          button.disabled = false;
        }
      }

      form.addEventListener('submit', (event) => {
        event.preventDefault();
        const url = urlInput.value.trim();
        if (!url) {
          status.innerHTML = '<span class=\"error\">Please provide a URL.</span>';
          return;
        }
        lookup(url);
      });
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the interactive HTML interface."""

    return HTMLResponse(content=_INDEX_HTML)


@app.get("/api/streams")
async def list_streams(url: str = Query(..., description="Media URL to inspect.")) -> MediaResponse:
    """Return all downloadable streams for the provided URL."""

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, get_media_info, url)
    except Exception as exc:  # pragma: no cover - defensive guard for yt-dlp errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MediaResponse.from_media_info(info)
