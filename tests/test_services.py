import unittest

from src.utils.validators import sanitize_text, validate_coordinates, validate_phone


class TestValidators(unittest.TestCase):
    def test_sanitize_text_removes_angle_brackets(self):
        text = "<b>unsafe</b> content"
        self.assertEqual(sanitize_text(text), "bunsafe/b content")

    def test_sanitize_text_applies_length_limit(self):
        self.assertEqual(sanitize_text("abcdef", max_length=3), "abc")

    def test_validate_coordinates_accepts_valid_range(self):
        self.assertTrue(validate_coordinates(55.7558, 37.6176))

    def test_validate_coordinates_rejects_invalid_range(self):
        self.assertFalse(validate_coordinates(95.0, 200.0))

    def test_validate_phone_accepts_russian_formats(self):
        self.assertTrue(validate_phone("+7 (999) 123-45-67"))
        self.assertTrue(validate_phone("89991234567"))

    def test_validate_phone_rejects_invalid(self):
        self.assertFalse(validate_phone("12345"))


if __name__ == "__main__":
    unittest.main()
