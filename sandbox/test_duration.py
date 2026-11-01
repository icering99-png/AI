import unittest
from sandbox.duration import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_example(self):
        self.assertEqual(parse_duration("1h 30m 15s"), 5415)

    def test_single_tokens(self):
        self.assertEqual(parse_duration("10s"), 10)
        self.assertEqual(parse_duration("5m"), 300)
        self.assertEqual(parse_duration("2h"), 7200)

    def test_zero_values(self):
        self.assertEqual(parse_duration("0s"), 0)
        self.assertEqual(parse_duration("0h 0m 0s"), 0)

    def test_type_error(self):
        with self.assertRaises(TypeError):
            parse_duration(None)  # type: ignore
        with self.assertRaises(TypeError):
            parse_duration(123)  # type: ignore

    def test_value_error_malformed_syntax(self):
        with self.assertRaises(ValueError):
            parse_duration("")
        with self.assertRaises(ValueError):
            parse_duration("   ")
        with self.assertRaises(ValueError):
            parse_duration("10")
        with self.assertRaises(ValueError):
            parse_duration("-5s")
        with self.assertRaises(ValueError):
            parse_duration("1d")
        with self.assertRaises(ValueError):
            parse_duration("1h trailing")

    def test_repeated_units_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1h 2h")
        with self.assertRaises(ValueError):
            parse_duration("1m 2s 3m")

    def test_valid_distinct_units_combination(self):
        self.assertEqual(parse_duration("2h 45s"), 7245)
        self.assertEqual(parse_duration("10m 5s"), 605)


if __name__ == "__main__":
    unittest.main()
