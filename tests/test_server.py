from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from urllib.parse import urlencode

from src.server import ShortenerHandler
from src.shortener import URLShortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = SimpleNamespace(shortener=URLShortener())

    def request(self, method, path, body=None, headers=None):
        payload = (body or "").encode("utf-8")
        request = [f"{method} {path} HTTP/1.1", "Host: localhost:8000"]
        if body is not None:
            request.append(f"Content-Length: {len(payload)}")
        request.extend(f"{name}: {value}" for name, value in (headers or {}).items())
        raw = "\r\n".join(request).encode("ascii") + b"\r\n\r\n" + payload
        received = BytesIO(raw)
        connection = Mock()
        connection.makefile.return_value = received

        ShortenerHandler(connection, ("127.0.0.1", 8000), self.server)

        response = b"".join(call.args[0] for call in connection.sendall.call_args_list)
        response_head, response_body = response.split(b"\r\n\r\n", maxsplit=1)
        status_line, *lines = response_head.decode("iso-8859-1").split("\r\n")
        status = int(status_line.split()[1])
        response_headers = [tuple(line.split(": ", maxsplit=1)) for line in lines]
        return status, response_headers, response_body.decode("utf-8")

    def post_url(self, url):
        body = urlencode({"url": url})
        return self.request(
            "POST",
            "/shorten",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

    def test_home_form_and_shortening(self):
        status, _headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('action="/shorten"', body)

        status, _headers, body = self.post_url("https://example.com/a")
        self.assertEqual(status, 200)
        self.assertIn('href="/0"', body)
        self.assertIn("https://example.com/a", body)

    def test_redirect_and_unknown_code(self):
        self.post_url("https://example.com/redirect")
        status, headers, _body = self.request("GET", "/0")
        self.assertEqual(status, 302)
        self.assertIn(("Location", "https://example.com/redirect"), headers)
        status, _headers, _body = self.request("GET", "/missing")
        self.assertEqual(status, 404)

    def test_invalid_submission_returns_bad_request(self):
        status, _headers, body = self.post_url("not a URL")
        self.assertEqual(status, 400)
        self.assertIn("Invalid URL", body)

    def test_table_shows_chains_and_hash_calculation(self):
        self.post_url("https://example.com/table")
        status, _headers, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("Separate chaining table", body)
        self.assertIn("Bucket 0", body)
        self.assertIn("hash:", body)
        self.assertIn("% 8 =", body)
        self.assertIn("<details>", body)
        self.assertIn("→", body)
        self.assertIn("NULL", body)
        self.assertIn('href="/0"', body)
        bucket = self.server.shortener.table_layout()
        expected = next(index for index, entries in bucket if entries)
        expected_from_url = 0
        for character in "https://example.com/table":
            expected_from_url = (31 * expected_from_url + ord(character)) % 8
        self.assertEqual(expected, expected_from_url)

    def test_short_link_uses_forwarded_https_origin(self):
        status, _headers, body = self.request(
            "POST", "/shorten", urlencode({"url": "https://example.com/share"}),
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Forwarded-Host": "example-8000.app.github.dev",
                "X-Forwarded-Proto": "https",
            },
        )
        self.assertEqual(status, 200)
        self.assertIn('href="https://example-8000.app.github.dev/0"', body)

    def test_invalid_forwarded_origin_preserves_relative_link(self):
        status, _headers, body = self.request(
            "POST", "/shorten", urlencode({"url": "https://example.com/share"}),
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Forwarded-Host": "bad.example/path",
                "X-Forwarded-Proto": "https",
            },
        )
        self.assertEqual(status, 200)
        self.assertIn('href="/0"', body)
        self.assertNotIn("bad.example", body)

    def test_table_shows_linear_probe_cells(self):
        self.server.shortener = URLShortener(table_type="linear")
        self.post_url("https://example.com/linear")
        self.post_url("https://example.com/lineaz")
        status, _headers, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("Linear probing table", body)
        self.assertIn("cells inspected:", body)
        self.assertRegex(body, r"cells inspected: (\d+) → \d+")


if __name__ == "__main__":
    unittest.main()
