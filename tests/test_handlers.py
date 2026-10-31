import unittest

try:
    from src.keyboards.main_menu import get_confirm_keyboard, get_accident_confirm_keyboard
    from src.keyboards.report_types import get_problem_type_keyboard, get_location_request_keyboard
    from src.states.report_states import ReportStates
    from src.states.accident_states import AccidentStates
    AIROGRAM_AVAILABLE = True
except ModuleNotFoundError:
    AIROGRAM_AVAILABLE = False


@unittest.skipUnless(AIROGRAM_AVAILABLE, "aiogram is not installed in this environment")
class TestKeyboardsAndStates(unittest.TestCase):
    def test_report_confirm_keyboard_contains_submit_button(self):
        keyboard = get_confirm_keyboard()
        first_button_text = keyboard.keyboard[0][0].text
        self.assertEqual(first_button_text, "✅ Сформировать заявление")

    def test_accident_confirm_keyboard_contains_yes_button(self):
        keyboard = get_accident_confirm_keyboard()
        first_button_text = keyboard.keyboard[0][0].text
        self.assertEqual(first_button_text, "✅ Да")

    def test_problem_type_keyboard_contains_cancel(self):
        keyboard = get_problem_type_keyboard()
        self.assertEqual(keyboard.keyboard[-1][0].text, "❌ Отмена")

    def test_location_keyboard_has_request_location(self):
        keyboard = get_location_request_keyboard()
        self.assertTrue(keyboard.keyboard[0][0].request_location)

    def test_report_states_have_expected_step(self):
        self.assertEqual(ReportStates.confirming_report.state, "ReportStates:confirming_report")

    def test_accident_states_have_expected_step(self):
        self.assertEqual(AccidentStates.confirming_accident.state, "AccidentStates:confirming_accident")


if __name__ == "__main__":
    unittest.main()
