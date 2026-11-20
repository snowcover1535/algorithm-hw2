"""A string-keyed hash table using separate chaining."""

from typing import Generic, Iterator, TypeVar


Value = TypeVar("Value")


class _Node(Generic[Value]):
    def __init__(self, key: str, value: Value, next_node: "_Node[Value] | None" = None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable(Generic[Value]):
    def __init__(self, capacity: int = 8):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._buckets: list[_Node[Value] | None] = [None] * capacity
        self._size = 0

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_trace(self, key: str, capacity: int | None = None) -> list[tuple[str, int]]:
        self._validate_key(key)
        modulus = self.capacity if capacity is None else capacity
        if modulus < 1:
            raise ValueError("capacity must be positive")
        value = 0
        trace = []
        for character in key:
            value = (value * 31 + ord(character)) % modulus
            trace.append((character, value))
        return trace

    def hash_index(self, key: str, capacity: int | None = None) -> int:
        trace = self.hash_trace(key, capacity)
        return trace[-1][1] if trace else 0

    def _find_node(self, key: str) -> _Node[Value] | None:
        node = self._buckets[self.hash_index(key)]
        while node is not None:
            if node.key == key:
                return node
            node = node.next
        return None

    def set(self, key: str, value: Value) -> None:
        self._validate_key(key)
        index = self.hash_index(key)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        new_node = _Node(key, value)
        if self._buckets[index] is None:
            self._buckets[index] = new_node
        else:
            node = self._buckets[index]
            while node.next is not None:
                node = node.next
            node.next = new_node
        self._size += 1
        if self._size / self.capacity > 0.75:
            self._resize(self.capacity * 2)

    def get(self, key: str) -> Value:
        self._validate_key(key)
        node = self._find_node(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def contains(self, key: str) -> bool:
        self._validate_key(key)
        return self._find_node(key) is not None

    def delete(self, key: str) -> Value:
        self._validate_key(key)
        index = self.hash_index(key)
        previous = None
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                if previous is None:
                    self._buckets[index] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return node.value
            previous, node = node, node.next
        raise KeyError(key)

    def _resize(self, capacity: int) -> None:
        old_buckets = self._buckets
        self.capacity = capacity
        self._buckets = [None] * capacity
        for head in old_buckets:
            node = head
            while node is not None:
                self._insert_without_resize(node.key, node.value)
                node = node.next

    def _insert_without_resize(self, key: str, value: Value) -> None:
        index = self.hash_index(key)
        new_node = _Node(key, value)
        if self._buckets[index] is None:
            self._buckets[index] = new_node
            return
        node = self._buckets[index]
        while node.next is not None:
            node = node.next
        node.next = new_node

    def items(self) -> Iterator[tuple[str, Value]]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    def bucket_entries(self) -> list[list[tuple[str, Value]]]:
        buckets = []
        for head in self._buckets:
            entries = []
            node = head
            while node is not None:
                entries.append((node.key, node.value))
                node = node.next
            buckets.append(entries)
        return buckets

    def __len__(self) -> int:
        return self._size
