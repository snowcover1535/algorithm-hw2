import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_table_and_missing_key(self):
        table = HashTable()
        self.assertEqual(len(table), 0)
        self.assertFalse(table.contains("missing"))
        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_collisions_updates_and_deletes(self):
        table = HashTable()
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
        table = HashTable()
        for index in range(40):
            table.set(f"key-{index}", index)
        self.assertGreaterEqual(table.capacity, 16)
        self.assertEqual(len(table), 40)
        for index in range(40):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_accepts_empty_string_key_and_rejects_non_string_keys(self):
        table = HashTable()
        table.set("", "empty")
        self.assertEqual(table.get(""), "empty")
        for operation in (table.get, table.contains, table.delete):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(TypeError):
                    operation(1)
        with self.assertRaises(TypeError):
            table.set(1, "not a string")


if __name__ == "__main__":
    unittest.main()
