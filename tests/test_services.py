import unittest

from src.utils.validators import sanitize_text, validate_coordinates
from src.utils.converters import parse_participant

try:
    from src.services.document_generator import _as_list
    REPORTLAB_AVAILABLE = True
except ModuleNotFoundError:
    REPORTLAB_AVAILABLE = False


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


class TestParseParticipant(unittest.TestCase):
    expected = {"name": "Иванов Иван", "phone": "+79990000000", "license_plate": "А123АА777", "insurance": "СОГАЗ"}

    def test_comma_separated(self):
        self.assertEqual(parse_participant("Иванов Иван, +79990000000, А123АА777, СОГАЗ"), self.expected)

    def test_one_field_per_line(self):
        self.assertEqual(parse_participant("Иванов Иван \n+79990000000\n\nА123АА777\nСОГАЗ"), self.expected)

    def test_missing_fields(self):
        result = parse_participant("Иванов Иван")
        self.assertEqual(result["name"], "Иванов Иван")
        self.assertEqual(result["insurance"], "Не указано")


class TestSettings(unittest.TestCase):
    def test_admin_ids_env_formats(self):
        from unittest.mock import patch
        from src.config import Settings
        cases = {"111": [111], "111,222": [111, 222], "[111,222]": [111, 222], "": []}
        for raw, expected in cases.items():
            with patch.dict("os.environ", {"ADMIN_IDS": raw}):
                self.assertEqual(Settings(_env_file=None).ADMIN_IDS, expected, raw)


@unittest.skipUnless(REPORTLAB_AVAILABLE, "reportlab is not installed in this environment")
class TestDocumentGenerator(unittest.TestCase):
    def test_as_list_keeps_list_from_handler(self):
        participants = [{"name": "Иванов"}]
        self.assertEqual(_as_list(participants), participants)

    def test_as_list_parses_json_from_db(self):
        self.assertEqual(_as_list('["a.jpg", "b.jpg"]'), ["a.jpg", "b.jpg"])

    def test_as_list_handles_missing_and_broken(self):
        self.assertEqual(_as_list(None), [])
        self.assertEqual(_as_list("not json"), [])


if __name__ == "__main__":
    unittest.main()
