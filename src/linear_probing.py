"""A string-keyed hash table using linear probing."""

from typing import Generic, Iterator, TypeVar

from src.hash_table import polynomial_hash_trace


Value = TypeVar("Value")


class _Tombstone:
    pass


_TOMBSTONE = _Tombstone()


class LinearProbingHashTable(Generic[Value]):
    def __init__(self, capacity: int = 8):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._slots: list[tuple[str, Value] | _Tombstone | None] = [None] * capacity
        self._size = 0

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_trace(self, key: str, capacity: int | None = None) -> list[tuple[str, int]]:
        self._validate_key(key)
        return polynomial_hash_trace(key, self.capacity if capacity is None else capacity)

    def hash_index(self, key: str, capacity: int | None = None) -> int:
        trace = self.hash_trace(key, capacity)
        return trace[-1][1] if trace else 0

    def _find_index(self, key: str) -> int | None:
        start = self.hash_index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            entry = self._slots[index]
            if entry is None:
                return None
            if entry is not _TOMBSTONE and entry[0] == key:
                return index
        return None

    def set(self, key: str, value: Value) -> None:
        self._validate_key(key)
        start = self.hash_index(key)
        first_tombstone = None
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            entry = self._slots[index]
            if entry is not _TOMBSTONE and entry is not None:
                if entry[0] == key:
                    self._slots[index] = (key, value)
                    return
                continue
            if entry is _TOMBSTONE:
                if first_tombstone is None:
                    first_tombstone = index
                continue
            destination = first_tombstone if first_tombstone is not None else index
            self._slots[destination] = (key, value)
            self._size += 1
            return

        if first_tombstone is not None:
            self._slots[first_tombstone] = (key, value)
            self._size += 1
            return
        self._resize(self.capacity * 2)
        self.set(key, value)

    def get(self, key: str) -> Value:
        self._validate_key(key)
        index = self._find_index(key)
        if index is None:
            raise KeyError(key)
        entry = self._slots[index]
        return entry[1]

    def contains(self, key: str) -> bool:
        self._validate_key(key)
        return self._find_index(key) is not None

    def delete(self, key: str) -> Value:
        self._validate_key(key)
        index = self._find_index(key)
        if index is None:
            raise KeyError(key)
        entry = self._slots[index]
        self._slots[index] = _TOMBSTONE
        self._size -= 1
        return entry[1]

    def _resize(self, capacity: int) -> None:
        old_slots = self._slots
        self.capacity = capacity
        self._slots = [None] * capacity
        self._size = 0
        for entry in old_slots:
            if entry is not None and entry is not _TOMBSTONE:
                self.set(entry[0], entry[1])

    def items(self) -> Iterator[tuple[str, Value]]:
        for entry in self._slots:
            if entry is not None and entry is not _TOMBSTONE:
                yield entry

    def lookup_trace(self, key: str) -> list[int]:
        self._validate_key(key)
        start = self.hash_index(key)
        inspected = []
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            inspected.append(index)
            entry = self._slots[index]
            if entry is None:
                break
            if entry is not _TOMBSTONE and entry[0] == key:
                break
        return inspected

    def bucket_entries(self) -> list[list[tuple[str, Value]]]:
        return [
            []
            if entry is None or entry is _TOMBSTONE
            else [entry]
            for entry in self._slots
        ]

    def __len__(self) -> int:
        return self._size
