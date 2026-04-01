from aiogram.fsm.state import State, StatesGroup

class ReportStates(StatesGroup):
    waiting_for_problem_type = State()
    waiting_for_photo = State()
    waiting_for_location_method = State()
    waiting_for_location_text = State()
    waiting_for_location_geo = State()
    waiting_for_description = State()
    confirming_report = State()