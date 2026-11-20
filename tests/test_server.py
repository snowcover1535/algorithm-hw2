import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server
from src.shortener import URLShortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server("127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=3
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.thread.join(timeout=3)
        self.server.server_close()

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        return response.status, response.getheaders(), response.read().decode("utf-8")

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

    def test_table_shows_linear_probe_cells(self):
        self.server.shortener = URLShortener(table_type="linear")
        self.post_url("https://example.com/linear")
        self.post_url("https://example.org/linear")
        status, _headers, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("Linear probing table", body)
        self.assertIn("cells inspected:", body)


if __name__ == "__main__":
    unittest.main()
