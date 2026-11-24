"""Standard-library HTTP interface for the URL shortener."""

import argparse
import html
import re
from datetime import datetime
from time import perf_counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from src.shortener import URLShortener


class ShortenerServer(HTTPServer):
    def __init__(self, address, handler, shortener: URLShortener):
        super().__init__(address, handler)
        self.shortener = shortener


class ShortenerHandler(BaseHTTPRequestHandler):
    def _send_html(self, status: int, document: str) -> None:
        body = document.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self) -> None:
        self._send_html(404, "<!doctype html><title>Not found</title><h1>Not found</h1>")

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(
                200,
                '<!doctype html><title>URL shortener</title>'
                '<h1>URL shortener</h1>'
                '<form method="post" action="/shorten">'
                '<label>URL <input name="url" type="url" required></label>'
                '<button type="submit">Shorten</button></form>'
                '<p><a href="/table">Inspect the hash table</a></p>',
            )
            return
        if path == "/table":
            self._send_table()
            return

        code = path.removeprefix("/")
        if not code or "/" in code:
            self._not_found()
            return
        try:
            url = self.server.shortener.expand(code)
        except KeyError:
            self._not_found()
            return
        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/shorten":
            self._not_found()
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_html(400, "<!doctype html><title>Bad request</title><h1>Bad request</h1>")
            return
        if content_length < 0:
            self._send_html(400, "<!doctype html><title>Bad request</title><h1>Bad request</h1>")
            return
        if content_length > 1_048_576:
            self._send_html(413, "<!doctype html><title>Too large</title><h1>Request too large</h1>")
            return
        try:
            body = self.rfile.read(content_length).decode("utf-8")
        except UnicodeDecodeError:
            self._send_html(400, "<!doctype html><title>Bad request</title><h1>Bad request</h1>")
            return

        form = parse_qs(body, keep_blank_values=True)
        url = form.get("url", [""])[0]
        try:
            code = self.server.shortener.shorten(url)
        except (TypeError, ValueError):
            self._send_html(
                400,
                '<!doctype html><title>Invalid URL</title>'
                '<h1>Invalid URL</h1><a href="/">Try again</a>',
            )
            return

        short_path = f"/{code}"
        short_link = html.escape(self._forwarded_origin() + short_path, quote=True)
        self._send_html(
            200,
            '<!doctype html><title>Short URL</title>'
            f'<h1>Short URL</h1><p>Short link: <a href="{short_link}">{short_link}</a></p>'
            f'<p>Original URL: {html.escape(url.strip())}</p>'
            '<p><a href="/">Shorten another</a> · <a href="/table">Inspect the hash table</a></p>',
        )

    def _forwarded_origin(self) -> str:
        host = self.headers.get("X-Forwarded-Host", "")
        scheme = self.headers.get("X-Forwarded-Proto", "")
        if scheme not in ("http", "https"):
            return ""
        # Only accept a single authority. Use relative links for local requests.
        if not re.fullmatch(r"(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:]+\])(?::[0-9]{1,5})?", host):
            return ""
        try:
            parsed = urlsplit(f"{scheme}://{host}")
            if not parsed.hostname or parsed.port == 0:
                return ""
        except ValueError:
            return ""
        return f"{scheme}://{host}"

    def _send_table(self) -> None:
        shortener = self.server.shortener
        chaining = shortener.table_type == "chaining"
        strategy = "Separate chaining" if chaining else "Linear probing"
        capacity = shortener.table_capacity
        origin = self._forwarded_origin()
        rows = [f"<h1>{strategy} table ({len(shortener)} entries, {capacity} buckets)</h1>"]
        for index, entries in shortener.table_layout():
            label = "Bucket" if chaining else "Slot"
            rows.append(f"<section><h2>{label} {index}</h2>")
            cards = []
            for code, url, trace, lookup_trace in entries:
                previous = 0
                steps = []
                for character, value in trace:
                    steps.append(
                        f"<li><code>{html.escape(character)}: ({previous} × 31 + "
                        f"{ord(character)}) % {capacity} = {value}</code></li>"
                    )
                    previous = value
                short_link = html.escape(f"{origin}/{code}", quote=True)
                if chaining:
                    lookup = f"nodes examined: {len(lookup_trace)}"
                else:
                    slots = " → ".join(str(slot) for slot in lookup_trace)
                    lookup = f"cells inspected: {slots}"
                cards.append(
                    f'<article><p>{html.escape(url)}<br>Code <code>{code}</code><br>'
                    f'<a href="{short_link}">{short_link}</a></p><details>'
                    f'<summary>hash: starting slot {previous}; {lookup}</summary>'
                    f'<ol>{"".join(steps)}</ol></details></article>'
                )
            if chaining:
                cards.append("<code>NULL</code>")
            rows.append(
                '<div class="chain">'
                + ('<span class="arrow" aria-hidden="true">→</span>'.join(cards) or "<p>empty</p>")
                + "</div></section>"
            )
        self._send_html(
            200,
            '<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Hash table</title><style>'
            'body{font:16px system-ui;max-width:72rem;margin:2rem auto;padding:0 1rem}'
            'section{border-top:1px solid #ccc;padding:.5rem 0}h2{font-size:1rem}'
            '.chain{display:flex;align-items:flex-start;gap:.6rem;flex-wrap:wrap}'
            'article{border:1px solid #888;border-radius:.4rem;padding:.65rem;overflow-wrap:anywhere}'
            'article p{margin:0 0 .4rem}summary{cursor:pointer}.arrow{font-size:1.3rem}'
            '</style><nav><a href="/">Home</a></nav>'
            + "".join(rows),
        )

def create_server(host: str = "", port: int = 8000, shortener: URLShortener | None = None):
    return ShortenerServer(
        (host, port),
        ShortenerHandler,
        shortener if shortener is not None else URLShortener(),
    )


def valid_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--port", type=valid_port, default=8000)
    parser.add_argument("--table-type", choices=("chaining", "linear"), default="chaining")
    arguments = parser.parse_args()
    started = perf_counter()
    print(f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] [0%] Starting {arguments.table_type} server", flush=True)
    server = create_server(port=arguments.port, shortener=URLShortener(arguments.table_type))
    print(
        f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] [100%] "
        f"Serving on port {server.server_port} ({perf_counter() - started:.2f}s)",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
