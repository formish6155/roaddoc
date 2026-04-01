from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_problem_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа проблемы"""
    keyboard = [
        [KeyboardButton(text="🕳️ Яма / выбоина")],
        [KeyboardButton(text="🚦 Неисправный светофор")],
        [KeyboardButton(text="🛣️ Проблемы с разметкой")],
        [KeyboardButton(text="🛑 Повреждённый знак")],
        [KeyboardButton(text="🌲 Помеха на дороге (ветка, мусор)")],
        [KeyboardButton(text="⚠️ Другое")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_location_request_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура запроса геолокации"""
    keyboard = [
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
        [KeyboardButton(text="✍️ Ввести адрес текстом")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)