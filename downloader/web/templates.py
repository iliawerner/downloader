"""HTML templates served by the FastAPI application."""

from __future__ import annotations

INDEX_HTML = """
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>YouTube Stream Inspector</title>
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
        background: linear-gradient(180deg, #0f172a, #1e293b);
        color: #f8fafc;
      }
      main {
        width: min(960px, 100%);
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(8px);
        border-radius: 1rem;
        padding: 2rem;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.35);
      }
      h1 {
        font-size: 2.25rem;
        margin-bottom: 1rem;
        letter-spacing: -0.03em;
      }
      p {
        margin: 0 0 1rem 0;
        line-height: 1.6;
      }
      form {
        display: flex;
        gap: 0.75rem;
        margin: 2rem 0 1.5rem;
        flex-wrap: wrap;
      }
      label {
        width: 100%;
        font-weight: 600;
        opacity: 0.85;
      }
      input[type=\"url\"],
      textarea {
        flex: 1;
        min-width: 280px;
        padding: 0.85rem 1rem;
        border-radius: 0.75rem;
        border: 1px solid rgba(148, 163, 184, 0.5);
        background: rgba(15, 23, 42, 0.6);
        color: inherit;
        font-size: 1rem;
      }
      textarea {
        min-height: 140px;
        width: 100%;
        resize: vertical;
        line-height: 1.4;
      }
      input[type=\"url\"]:focus,
      textarea:focus {
        outline: none;
        border-color: #38bdf8;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
      }
      button {
        padding: 0.85rem 1.5rem;
        border-radius: 0.75rem;
        border: none;
        background: linear-gradient(135deg, #38bdf8, #6366f1);
        color: white;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: transform 0.1s ease;
      }
      button:hover {
        transform: translateY(-1px);
      }
      button:disabled {
        opacity: 0.6;
        cursor: progress;
      }
      .status {
        min-height: 1.5rem;
        font-weight: 500;
      }
      .error {
        color: #f87171;
      }
      .cards {
        display: grid;
        gap: 1.5rem;
      }
      .card {
        border-radius: 1rem;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 1.5rem;
      }
      .logs {
        margin-top: 1.5rem;
      }
      .logs pre {
        background: rgba(15, 23, 42, 0.55);
        border-radius: 0.75rem;
        padding: 1rem;
        max-height: 320px;
        overflow: auto;
        white-space: pre-wrap;
        word-break: break-word;
        border: 1px solid rgba(148, 163, 184, 0.2);
      }
      .streams {
        overflow-x: auto;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
      }
      th, td {
        padding: 0.75rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        text-align: left;
      }
      th {
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.08em;
        opacity: 0.6;
      }
      code {
        background: rgba(148, 163, 184, 0.15);
        border-radius: 0.4rem;
        padding: 0.15rem 0.35rem;
      }
      footer {
        margin-top: 2.5rem;
        font-size: 0.85rem;
        opacity: 0.7;
      }
      a {
        color: #38bdf8;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>YouTube Stream Inspector</h1>
      <p>Paste your freshest cookies and the video URL to list every available video resolution and standalone audio stream. The tool never downloads content; it only reveals direct CDN links provided by the platform.</p>
      <form id=\"lookup\">
        <label for=\"cookies\">Cookies (optional)</label>
        <textarea id=\"cookies\" name=\"cookies\" placeholder=\"# Netscape HTTP Cookie File\"></textarea>
        <label for=\"url\">Video URL</label>
        <input id=\"url\" name=\"url\" type=\"url\" placeholder=\"https://www.youtube.com/watch?v=...\" required />
        <button type=\"submit\">Inspect</button>
      </form>
      <p class=\"status\" id=\"status\"></p>
      <section class=\"cards\" id=\"results\" hidden></section>
      <section class=\"card logs\" id=\"logs\" hidden>
        <h2>Debug Log</h2>
        <pre id=\"logs-content\"></pre>
      </section>
      <footer>
        Built for research purposes with <code>yt-dlp</code>. Please respect copyright and platform terms of service.
      </footer>
    </main>
    <script>
      const form = document.getElementById('lookup');
      const input = document.getElementById('url');
      const cookiesInput = document.getElementById('cookies');
      const status = document.getElementById('status');
      const results = document.getElementById('results');
      const button = form.querySelector('button');
      const logPanel = document.getElementById('logs');
      const logContent = document.getElementById('logs-content');

      function resetLogs() {
        logContent.textContent = '';
        logPanel.hidden = false;
      }

      function appendLog(message, details) {
        const timestamp = new Date().toISOString();
        logContent.textContent += `[${timestamp}] ${message}`;
        if (details) {
          const formatted = typeof details === 'string' ? details : JSON.stringify(details, null, 2);
          logContent.textContent += `\n${formatted}`;
        }
        logContent.textContent += '\n\n';
      }

      function escapeHtml(value) {
        return value.replace(/[&<>\"']/g, (char) => ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;',
        })[char]);
      }

      function renderStreams(title, streams) {
        const safeStreams = Array.isArray(streams) ? streams : [];
        if (!safeStreams.length) {
          return `<article class=\"card\"><h2>${title}</h2><p>No streams available.</p></article>`;
        }
        const headers = ['Format', 'MIME Type', 'Resolution', 'Bitrate', 'FPS', 'Filesize', 'Extra', 'Download'];
        const rows = safeStreams.map((stream) => {
          const formatId = typeof stream.format_id === 'string' ? stream.format_id : '—';
          const mimeType = typeof stream.mime_type === 'string' ? stream.mime_type : '—';
          const bitrate = typeof stream.bitrate_kbps === 'number' ? `${stream.bitrate_kbps} kbps` : '—';
          const fps = typeof stream.fps === 'number' ? stream.fps : '—';
          const size = typeof stream.filesize_bytes === 'number' ? `${(stream.filesize_bytes / (1024 * 1024)).toFixed(2)} MiB` : '—';
          const resolution = typeof stream.resolution === 'string' ? stream.resolution : '—';
          const extrasSource = stream.extra && typeof stream.extra === 'object' ? stream.extra : null;
          const extras = extrasSource
            ? Object.entries(extrasSource)
                .map(([key, value]) => `<div><strong>${escapeHtml(key)}:</strong> ${escapeHtml(String(value))}</div>`)
                .join('')
            : '—';
          const downloadUrl = typeof stream.url === 'string' ? stream.url : '#';
          return `<tr>
            <td>${escapeHtml(formatId)}</td>
            <td>${escapeHtml(mimeType)}</td>
            <td>${escapeHtml(resolution)}</td>
            <td>${escapeHtml(bitrate)}</td>
            <td>${escapeHtml(String(fps))}</td>
            <td>${escapeHtml(size)}</td>
            <td>${extras}</td>
            <td><a href=\"${escapeHtml(downloadUrl)}\" target=\"_blank\" rel=\"noopener noreferrer\">Download</a></td>
          </tr>`;
        }).join('');
        return `<article class=\"card streams\">
          <h2>${title}</h2>
          <table>
            <thead><tr>${headers.map((header) => `<th>${header}</th>`).join('')}</tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </article>`;
      }

      async function lookup(url, cookies) {
        const previousMarkup = results.innerHTML;
        const hadPreviousResults = !results.hidden;
        status.textContent = '';
        button.disabled = true;
        resetLogs();
        try {
          const requestBody = { url, cookies: cookies ?? null };
          appendLog('Sending POST /api/streams request', requestBody);
          const response = await fetch('/api/streams', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
          });
          appendLog(`Received response ${response.status} ${response.statusText}`);
          const responseText = await response.text();
          appendLog('Raw response body', responseText || '<empty>');
          let payload;
          try {
            payload = responseText ? JSON.parse(responseText) : {};
          } catch (parseError) {
            appendLog('Response JSON parse error', String(parseError));
            throw new Error('Failed to parse response JSON');
          }
          if (!response.ok) {
            throw new Error(payload.detail || 'Lookup failed');
          }
          const cards = [];
          const title = typeof payload.title === 'string' && payload.title.trim() ? payload.title : 'Untitled';
          const pageUrl = typeof payload.page_url === 'string' && payload.page_url ? payload.page_url : url;
          const videoStreams = Array.isArray(payload.video_streams) ? payload.video_streams : [];
          const audioStreams = Array.isArray(payload.audio_streams) ? payload.audio_streams : [];
          appendLog('Rendering results', {
            video_streams: videoStreams.length,
            audio_streams: audioStreams.length,
          });
          cards.push(`<article class=\"card\"><h2>${escapeHtml(title)}</h2><p><a href=\"${escapeHtml(pageUrl)}\" target=\"_blank\" rel=\"noopener noreferrer\">Open original page</a></p></article>`);
          cards.push(renderStreams('Video Streams', videoStreams));
          cards.push(renderStreams('Audio Streams', audioStreams));
          results.innerHTML = cards.join('');
          results.hidden = false;
        } catch (error) {
          appendLog('Lookup failed', error?.message || String(error));
          status.innerHTML = `<span class=\"error\">${escapeHtml(error.message || 'Unexpected error')}</span>`;
          if (hadPreviousResults) {
            results.innerHTML = previousMarkup;
            results.hidden = false;
          }
        } finally {
          button.disabled = false;
        }
      }

      form.addEventListener('submit', (event) => {
        event.preventDefault();
        const url = input.value.trim();
        const cookies = cookiesInput.value.trim();
        if (!url) {
          status.innerHTML = '<span class=\"error\">Please enter a URL.</span>';
          return;
        }
        lookup(url, cookies || null);
      });
    </script>
  </body>
</html>
"""
