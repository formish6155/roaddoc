from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Эмодзи и название через один пробел: обработчик сохраняет в БД часть после пробела
PROBLEM_TYPES = [
    "🕳️ Яма / выбоина",
    "🚦 Неисправный светофор",
    "🛣️ Проблемы с разметкой",
    "🛑 Повреждённый знак",
    "🌲 Помеха на дороге (ветка, мусор)",
    "⚠️ Другое",
]

def get_problem_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа проблемы"""
    keyboard = [[KeyboardButton(text=t)] for t in PROBLEM_TYPES] + [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_location_request_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура запроса геолокации"""
    keyboard = [
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
        [KeyboardButton(text="✍️ Ввести адрес текстом")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)