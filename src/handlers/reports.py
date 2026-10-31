from aiogram import Router, F
from aiogram.types import Message, PhotoSize, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from pathlib import Path
from html import escape
import asyncio
import uuid
from src.database import Report, User, get_db
from src.states.report_states import ReportStates
from src.keyboards.report_types import PROBLEM_TYPES, get_problem_type_keyboard, get_location_request_keyboard
from src.keyboards.main_menu import main_menu, cancel_menu
from src.services.document_generator import generate_problem_statement
from src.utils.validators import sanitize_text, validate_coordinates
from src.utils.logger import get_logger
from src.keyboards.main_menu import get_confirm_keyboard

logger = get_logger(__name__)
router = Router()

async def start_report(message: Message, state: FSMContext):
    """Начало оформления жалобы"""
    await message.answer(
        "Выберите тип проблемы на дороге:",
        reply_markup=get_problem_type_keyboard()
    )
    await state.set_state(ReportStates.waiting_for_problem_type)
    logger.info(f"User {message.from_user.id} started report creation")

@router.message(
    StateFilter(ReportStates.waiting_for_location_text, ReportStates.waiting_for_description),
    ~F.text
)
async def require_text(message: Message):
    await message.answer("✏️ Пожалуйста, отправьте ответ текстом.", reply_markup=cancel_menu)

@router.message(ReportStates.waiting_for_problem_type)
async def process_problem_type(message: Message, state: FSMContext):
    """Обработка выбора типа проблемы"""
    if message.text not in PROBLEM_TYPES:
        await message.answer(
            "Пожалуйста, выберите тип проблемы из списка ниже:",
            reply_markup=get_problem_type_keyboard()
        )
        return
    
    # Сохраняем тип без эмодзи
    problem_type = message.text.split(" ", 1)[1]
    
    await state.update_data(problem_type=problem_type)
    await message.answer(
        "📸 Отправьте фотографию проблемы (можно сделать прямо сейчас):",
        reply_markup=cancel_menu
    )
    await state.set_state(ReportStates.waiting_for_photo)

@router.message(ReportStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка фотографии проблемы"""
    photo: PhotoSize = message.photo[-1]  # Самая большая версия
    
    # Генерируем уникальное имя файла
    filename = f"report_{uuid.uuid4().hex}.jpg"
    filepath = Path("./data/photos") / filename
    
    # Скачиваем фото
    await message.bot.download(
        photo,
        destination=filepath
    )
    
    await state.update_data(photo_path=str(filepath))
    await message.answer(
        "📍 Укажите местоположение проблемы:",
        reply_markup=get_location_request_keyboard()
    )
    await state.set_state(ReportStates.waiting_for_location_method)

@router.message(ReportStates.waiting_for_photo)
async def invalid_photo(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте именно фотографию (не документ и не текст).",
        reply_markup=cancel_menu
    )

@router.message(ReportStates.waiting_for_location_method, F.location)
async def process_location_geo(message: Message, state: FSMContext):
    """Обработка геолокации"""
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    if not validate_coordinates(latitude, longitude):
        await message.answer(
            "❌ Некорректные координаты. Попробуйте отправить ещё раз.",
            reply_markup=get_location_request_keyboard()
        )
        return
    
    await state.update_data(latitude=latitude, longitude=longitude)
    await message.answer(
        "✏️ Кратко опишите проблему (что именно повреждено, как давно, есть ли угроза безопасности):",
        reply_markup=cancel_menu
    )
    await state.set_state(ReportStates.waiting_for_description)

@router.message(ReportStates.waiting_for_location_method, F.text == "📍 Отправить геолокацию")
async def request_geo_location(message: Message):
    await message.answer(
        "Пожалуйста, нажмите на скрепку 📎 → 'Геопозиция' → 'Отправить мою геопозицию'",
        reply_markup=get_location_request_keyboard()
    )

@router.message(ReportStates.waiting_for_location_method, F.text == "✍️ Ввести адрес текстом")
async def request_text_address(message: Message, state: FSMContext):
    await message.answer(
        "Введите адрес проблемы текстом (пример: г. Москва, ул. Ленина, д. 15):",
        reply_markup=cancel_menu
    )
    await state.set_state(ReportStates.waiting_for_location_text)

@router.message(ReportStates.waiting_for_location_text)
async def process_location_text(message: Message, state: FSMContext):
    """Обработка текстового адреса"""
    address = sanitize_text(message.text, max_length=200)
    await state.update_data(address=address)
    await message.answer(
        "✏️ Кратко опишите проблему (что именно повреждено, как давно, есть ли угроза безопасности):",
        reply_markup=cancel_menu
    )
    await state.set_state(ReportStates.waiting_for_description)

@router.message(ReportStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания проблемы"""
    description = sanitize_text(message.text, max_length=1000)
    await state.update_data(description=description)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Формируем подтверждение
    confirmation_text = (
        "📋 <b>Проверьте данные заявления:</b>\n\n"
        f"<b>Тип проблемы:</b> {data['problem_type']}\n"
    )
    
    if data.get('latitude') and data.get('longitude'):
        confirmation_text += f"<b>Координаты:</b> {data['latitude']:.6f}, {data['longitude']:.6f}\n"
    elif data.get('address'):
        confirmation_text += f"<b>Адрес:</b> {escape(data['address'])}\n"

    if data.get('description'):
        confirmation_text += f"<b>Описание:</b> {escape(data['description'])}\n"
    
    confirmation_text += "\n✅ Сформировать заявление?"
    
    await message.answer(
        confirmation_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ReportStates.confirming_report)

@router.message(
    ReportStates.confirming_report,
    F.text.in_(["✅ Сформировать заявление", "Да", "да"])
)
async def confirm_report(message: Message, state: FSMContext):
    """Подтверждение и сохранение заявления"""
    data = await state.get_data()
    # Сбрасываем сразу. Повторное нажатие, прошедшее фильтр состояния до сброса, увидит пустые данные и выйдет
    await state.clear()
    if not data:
        return

    # Сохраняем в БД
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one()
        
        report = Report(
            user_id=user.id,
            problem_type=data['problem_type'],
            description=data.get('description'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            address=data.get('address'),
            photo_path=data.get('photo_path'),
            status="new"
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        
        # Генерируем заявление
        report_data = {
            'id': report.id,
            'user_full_name': user.full_name,
            'username': user.username or str(user.telegram_id),
            'problem_type': report.problem_type,
            'description': report.description,
            'latitude': report.latitude,
            'longitude': report.longitude,
            'address': report.address,
            'photo_path': report.photo_path,
            'created_at': report.created_at
        }
        
        # В отдельном потоке: сборка PDF занимает сотни мс и иначе стопорит ответы всем пользователям
        document_path = await asyncio.to_thread(generate_problem_statement, report_data)
        report.document_path = document_path
        await session.commit()
    
    # Отправляем документ пользователю
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")

    await message.bot.send_document(
        chat_id=message.chat.id,
        document=FSInputFile(document_path),
        caption=f"✅ Заявление RD-{report.id} сформировано"
    )

    await message.answer(
        "Бот не отправляет заявление сам. Направьте этот документ в дорожную службу "
        "или администрацию вашего района — например, через Госуслуги или по электронной почте.",
        reply_markup=main_menu
    )
    
    logger.info(f"Report #{report.id} created by user {message.from_user.id}")

@router.message(ReportStates.confirming_report)
async def handle_confirmation(message: Message):
    await message.answer(
        "Пожалуйста, подтвердите кнопкой '✅ Сформировать заявление' или отмените операцию кнопкой '❌ Отмена'",
        reply_markup=get_confirm_keyboard()
    )
