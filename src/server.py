"""Standard-library HTTP interface for the URL shortener."""

import argparse
import html
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
                '<button type="submit">Shorten</button></form>',
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

        short_link = f"/{html.escape(code, quote=True)}"
        self._send_html(
            200,
            '<!doctype html><title>Short URL</title>'
            f'<h1>Short URL</h1><p>Short link: <a href="{short_link}">{short_link}</a></p>'
            f'<p>Original URL: {html.escape(url.strip())}</p><a href="/">Shorten another</a>',
        )

    def _send_table(self) -> None:
        strategy = (
            "Separate chaining"
            if self.server.shortener.table_type == "chaining"
            else "Linear probing"
        )
        rows = [
            f'<h1>{strategy} table ({len(self.server.shortener)} entries, '
            f'{self.server.shortener.table_capacity} buckets)</h1>'
        ]
        for bucket_index, entries in self.server.shortener.table_layout():
            rows.append(f"<h2>Bucket {bucket_index}</h2>")
            if not entries:
                rows.append("<p>empty</p>")
                continue
            rows.append("<ol>")
            for code, url, trace, lookup_trace in entries:
                previous = 0
                steps = []
                for character, value in trace:
                    steps.append(
                        f"({previous}*31 + {ord(character)}) % "
                        f"{self.server.shortener.table_capacity} = {value}"
                    )
                    previous = value
                calculation = " ; ".join(steps) or "empty string"
                inspected_label = (
                    "cells inspected"
                    if self.server.shortener.table_type == "linear"
                    else "nodes examined"
                )
                rows.append(
                    f"<li><code>{html.escape(code)}</code>: "
                    f"{html.escape(url)}; hash: {calculation}; "
                    f"bucket: {bucket_index}; {inspected_label}: "
                    f"{' -> '.join(str(slot) for slot in lookup_trace)}</li>"
                )
            rows.append("</ol>")
        self._send_html(
            200,
            '<!doctype html><title>Hash table</title>'
            + "".join(rows)
            + '<p><a href="/">Home</a></p>',
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
    arguments = parser.parse_args()
    server = create_server(port=arguments.port)
    print(f"Serving on http://{server.server_address[0]}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
