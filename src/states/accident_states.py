from aiogram.fsm.state import State, StatesGroup

class AccidentStates(StatesGroup):
    waiting_for_participants_count = State()
    waiting_for_participant_data = State()
    waiting_for_photos = State()
    waiting_for_location = State()
    waiting_for_description = State()
    confirming_accident = State()