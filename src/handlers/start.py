from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from pathlib import Path
from src.keyboards.main_menu import main_menu
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

async def discard_form(state: FSMContext):
    """Сбросить незаконченную форму и удалить скачанные для неё фото — в БД они не попадут"""
    data = await state.get_data()
    for path in data.get('photo_paths', []) + [data.get('photo_path')]:
        if path:
            Path(path).unlink(missing_ok=True)
    await state.clear()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start (пользователя регистрирует FirstContactMiddleware)"""
    await discard_form(state)

    welcome_text = (
        "👋 Добро пожаловать в <b>RoadDoc</b>!\n\n"
        "Я помогу вам:\n"
        "✅ Сообщить о проблемах на дорогах (ямы, светофоры, разметка)\n"
        "✅ Оформить ДТП по европротоколу без вызова ГИБДД\n"
        "✅ Получить контакты дорожных служб и юридическую консультацию\n"
        "✅ Отследить статус ваших обращений\n\n"
        "Выберите действие ниже или используйте команды:\n"
        "/report — Сообщить о проблеме\n"
        "/accident — Оформить ДТП\n"
        "/help — Справка"
    )
    
    await message.answer(welcome_text, reply_markup=main_menu, parse_mode="HTML")

@router.message(F.text == "🏠 Главное меню")
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await discard_form(state)
    await message.answer("Вы в главном меню:", reply_markup=main_menu)

@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции (единственный обработчик «❌ Отмена»: роутер start подключён первым)"""
    current_state = await state.get_state()
    if current_state:
        await discard_form(state)
        await message.answer("❌ Операция отменена", reply_markup=main_menu)
        logger.info(f"Пользователь {message.from_user.id} отменил операцию {current_state}")
    else:
        await message.answer("Нет активных операций для отмены", reply_markup=main_menu)

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Справка и контакты")
async def cmd_help(message: Message):
    """Справочная информация"""
    help_text = (
        "ℹ️ <b>Справка по RoadDoc</b>\n\n"
        "<b>Как сообщить о проблеме:</b>\n"
        "1. Нажмите «📝 Сообщить о проблеме»\n"
        "2. Выберите тип проблемы (яма, светофор и т.д.)\n"
        "3. Отправьте фото проблемы\n"
        "4. Укажите местоположение (геолокация или адрес)\n"
        "5. Опишите проблему подробно\n"
        "6. Получите готовое заявление в PDF и направьте его в дорожную службу\n\n"
        "<b>Как оформить ДТП:</b>\n"
        "1. Нажмите «🚗 Оформить ДТП»\n"
        "2. Укажите количество участников\n"
        "3. Введите данные каждого участника\n"
        "4. Отправьте фото места ДТП (минимум 3)\n"
        "5. Укажите обстоятельства происшествия\n"
        "6. Получите готовый европротокол в PDF\n\n"
        "<b>Экстренные контакты:</b>\n"
        "• ГИБДД: 112 или 102\n"
        "• Единая диспетчерская служба: 112\n"
        "• Дорожная инспекция: уточнить в вашем регионе\n\n"
        "<b>Важно:</b> Бот не заменяет официальные органы. "
        "В случае серьёзных происшествий всегда вызывайте ГИБДД!"
    )
    
    await message.answer(help_text, reply_markup=main_menu, parse_mode="HTML")

@router.message(Command("report"))
@router.message(F.text == "📝 Сообщить о проблеме")
async def cmd_report(message: Message, state: FSMContext):
    """Начало оформления жалобы на проблему"""
    from .reports import start_report
    await discard_form(state)  # иначе данные брошенной формы попадут в новую
    await start_report(message, state)

@router.message(Command("accident"))
@router.message(F.text == "🚗 Оформить ДТП")
async def cmd_accident(message: Message, state: FSMContext):
    """Начало оформления ДТП"""
    from .accidents import start_accident
    await discard_form(state)  # иначе данные брошенной формы попадут в новую
    await start_accident(message, state)

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message):
    """Показать статистику (только для админов)"""
    from .admin import show_statistics
    await show_statistics(message)
