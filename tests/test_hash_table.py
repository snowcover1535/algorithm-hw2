import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class HashTableContractTests:
    table_class = None

    def test_empty_table_and_missing_key(self):
        table = self.table_class()
        self.assertEqual(len(table), 0)
        self.assertFalse(table.contains("missing"))
        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_collisions_updates_and_deletes(self):
        table = self.table_class()
        for key, value in (("a", 1), ("i", 2), ("q", 3)):
            table.set(key, value)
        self.assertEqual([table.get(key) for key in ("a", "i", "q")], [1, 2, 3])
        table.set("i", 20)
        self.assertEqual(table.get("i"), 20)
        self.assertEqual(len(table), 3)
        self.assertEqual(table.delete("i"), 20)
        self.assertFalse(table.contains("i"))
        self.assertEqual(table.get("q"), 3)
        self.assertEqual(len(table), 2)

    def test_resizes_and_preserves_every_entry(self):
        table = self.table_class()
        for index in range(40):
            table.set(f"key-{index}", index)
        self.assertGreaterEqual(table.capacity, 16)
        self.assertEqual(len(table), 40)
        for index in range(40):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_accepts_empty_string_key_and_rejects_non_string_keys(self):
        table = self.table_class()
        table.set("", "empty")
        self.assertEqual(table.get(""), "empty")
        for operation in (table.get, table.contains, table.delete):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(TypeError):
                    operation(1)
        with self.assertRaises(TypeError):
            table.set(1, "not a string")


class ChainingHashTableTests(unittest.TestCase, HashTableContractTests):
    table_class = HashTable


class LinearProbingHashTableTests(unittest.TestCase, HashTableContractTests):
    table_class = LinearProbingHashTable

    def test_probe_wraps_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(capacity=8)
        table.set("g", "last")
        table.set("o", "wrapped")
        slots = table.bucket_entries()
        self.assertEqual(slots[7], [("g", "last")])
        self.assertEqual(slots[0], [("o", "wrapped")])
        self.assertEqual(table.lookup_trace("o"), [7, 0])

    def test_full_table_is_searchable_and_grows_for_next_entry(self):
        table = LinearProbingHashTable(capacity=4)
        for index in range(4):
            table.set(f"full-{index}", index)
        self.assertEqual(table.capacity, 4)
        self.assertEqual(len(table), 4)
        for index in range(4):
            self.assertEqual(table.get(f"full-{index}"), index)

        table.set("overflow", 4)
        self.assertEqual(table.capacity, 8)
        self.assertEqual(len(table), 5)
        self.assertEqual(table.get("overflow"), 4)


if __name__ == "__main__":
    unittest.main()
