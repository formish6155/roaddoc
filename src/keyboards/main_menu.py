from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    keyboard = [
        [KeyboardButton(text="📝 Сообщить о проблеме")],
        [KeyboardButton(text="🚗 Оформить ДТП")],
        [KeyboardButton(text="ℹ️ Справка и контакты")],
        [KeyboardButton(text="📊 Статистика")]  # Доступно админам
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Кнопка отмены для любых операций"""
    keyboard = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения отправки"""
    keyboard = [
        [KeyboardButton(text="✅ Отправить заявление")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_accident_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения оформления ДТП"""
    keyboard = [
        [KeyboardButton(text="✅ Да")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

main_menu = get_main_menu_keyboard()
cancel_menu = get_cancel_keyboard()
