import unittest

from src.base62 import ALPHABET, decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_encodes_to_zero_character(self):
        self.assertEqual(encode(0), "0")

    def test_round_trip_boundaries(self):
        values = (0, 1, 61, 62, 63, 3843, 3844, 2**64)
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_alphabet_order(self):
        for value, character in enumerate(ALPHABET):
            with self.subTest(value=value):
                self.assertEqual(encode(value), character)

    def test_rejects_negative_or_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(TypeError):
            encode(True)
        with self.assertRaises(TypeError):
            encode("1")

    def test_rejects_empty_or_invalid_codes(self):
        for code in ("", "a_", "é"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)


if __name__ == "__main__":
    unittest.main()
