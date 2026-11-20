"""URL shortening backed by the project's custom hash table."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class URLShortener:
    def __init__(self, table_type: str = "chaining"):
        if table_type == "chaining":
            table_class = HashTable
        elif table_type == "linear":
            table_class = LinearProbingHashTable
        else:
            raise ValueError("table_type must be 'chaining' or 'linear'")
        self.table_type = table_type
        self._code_by_url = table_class()
        self._url_by_code = table_class()
        self._next_id = 0

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if any(ord(character) < 32 or ord(character) == 127 for character in url):
            raise ValueError("URL must not contain control characters")
        normalized = url.strip()
        try:
            parsed = urlsplit(normalized)
            host = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("URL must have a valid HTTP(S) host") from error
        if (
            parsed.scheme.lower() not in ("http", "https")
            or not host
            or any(character.isspace() for character in parsed.netloc)
        ):
            raise ValueError("URL must have a valid HTTP(S) host")
        return normalized

    def shorten(self, url: str) -> str:
        normalized = self._normalize_url(url)
        if self._code_by_url.contains(normalized):
            return self._code_by_url.get(normalized)

        code = encode(self._next_id)
        self._next_id += 1
        self._code_by_url.set(normalized, code)
        self._url_by_code.set(code, normalized)
        return code

    def expand(self, code: str) -> str:
        if not isinstance(code, str):
            raise KeyError(code)
        try:
            decode(code)
            return self._url_by_code.get(code)
        except (ValueError, KeyError) as error:
            raise KeyError(code) from error

    def items(self):
        return self._url_by_code.items()

    def table_layout(
        self,
    ) -> list[tuple[int, list[tuple[str, str, list[tuple[str, int]], list[int]]]]]:
        layout = []
        for index, entries in enumerate(self._url_by_code.bucket_entries()):
            details = [
                (
                    code,
                    url,
                    self._url_by_code.hash_trace(code),
                    self._url_by_code.lookup_trace(code),
                )
                for code, url in entries
            ]
            layout.append((index, details))
        return layout

    @property
    def table_capacity(self) -> int:
        return self._url_by_code.capacity

    def __len__(self) -> int:
        return len(self._url_by_code)
