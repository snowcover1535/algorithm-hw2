"""URL shortening backed by the project's custom hash table."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable


class URLShortener:
    def __init__(self):
        self._code_by_url: HashTable[str] = HashTable()
        self._url_by_code: HashTable[str] = HashTable()
        self._next_id = 0

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
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

    def __len__(self) -> int:
        return len(self._url_by_code)
