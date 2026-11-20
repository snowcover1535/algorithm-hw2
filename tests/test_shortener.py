import unittest

from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def test_shortens_and_expands_using_incrementing_base62_ids(self):
        shortener = URLShortener()
        first = shortener.shorten("https://example.com/a")
        second = shortener.shorten("http://example.org/b")
        self.assertEqual(first, "0")
        self.assertEqual(second, "1")
        self.assertEqual(shortener.expand(first), "https://example.com/a")
        self.assertEqual(shortener.expand(second), "http://example.org/b")

    def test_normalizes_surrounding_whitespace_and_reuses_url_code(self):
        shortener = URLShortener()
        code = shortener.shorten("  https://example.com/path  ")
        self.assertEqual(shortener.shorten("https://example.com/path"), code)
        self.assertEqual(shortener.expand(code), "https://example.com/path")

    def test_distinct_paths_and_case_get_distinct_codes(self):
        shortener = URLShortener()
        self.assertNotEqual(
            shortener.shorten("https://example.com/A"),
            shortener.shorten("https://example.com/a"),
        )

    def test_rejects_invalid_urls(self):
        shortener = URLShortener()
        for url in ("", "example.com", "ftp://example.com", "https:///missing-host"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)
        with self.assertRaises(TypeError):
            shortener.shorten(None)

    def test_unknown_or_malformed_codes_raise_key_error(self):
        shortener = URLShortener()
        for code in ("1", "_", ""):
            with self.subTest(code=code):
                with self.assertRaises(KeyError):
                    shortener.expand(code)


if __name__ == "__main__":
    unittest.main()
