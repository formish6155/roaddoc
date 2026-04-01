from aiogram import Router, F
from aiogram.types import Message, PhotoSize, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
import json
import uuid
from pathlib import Path
from src.database import AccidentReport, User, get_db
from src.states.accident_states import AccidentStates
from src.keyboards.main_menu import main_menu, cancel_menu, get_accident_confirm_keyboard
from src.services.document_generator import generate_accident_protocol
from src.utils.validators import sanitize_text
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

async def start_accident(message: Message, state: FSMContext):
    """Начало оформления ДТП"""
    await message.answer(
        "🚗 <b>Оформление ДТП по европротоколу</b>\n\n"
        "Укажите количество участников ДТП (включая вас):",
        reply_markup=cancel_menu,
        parse_mode="HTML"
    )
    await state.set_state(AccidentStates.waiting_for_participants_count)

@router.message(AccidentStates.waiting_for_participants_count, F.text == "❌ Отмена")
async def cancel_accident(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Оформление ДТП отменено", reply_markup=main_menu)

@router.message(AccidentStates.waiting_for_participants_count)
async def process_participants_count(message: Message, state: FSMContext):
    """Обработка количества участников"""
    try:
        count = int(message.text)
        if count < 2 or count > 5:
            await message.answer(
                "⚠️ Количество участников должно быть от 2 до 5. Укажите корректное число:",
                reply_markup=cancel_menu
            )
            return
    except ValueError:
        await message.answer(
            "⚠️ Пожалуйста, введите число (например: 2):",
            reply_markup=cancel_menu
        )
        return
    
    await state.update_data(participants_count=count, participants=[])
    await state.update_data(current_participant=1)
    
    await message.answer(
        f"👤 Введите данные <b>участника №1</b> (вас):\n"
        "Формат: ФИО, телефон, гос.номер, страховая компания",
        reply_markup=cancel_menu,
        parse_mode="HTML"
    )
    await state.set_state(AccidentStates.waiting_for_participant_data)

@router.message(AccidentStates.waiting_for_participant_data)
async def process_participant_data(message: Message, state: FSMContext):
    """Обработка данных участника"""
    data = await state.get_data()
    participants = data.get('participants', [])
    current = data.get('current_participant', 1)
    total = data.get('participants_count', 2)
    
    # Парсим данные участника (упрощённо)
    parts = [p.strip() for p in message.text.split(',')]
    participant = {
        'name': parts[0] if len(parts) > 0 else 'Не указано',
        'phone': parts[1] if len(parts) > 1 else 'Не указано',
        'license_plate': parts[2] if len(parts) > 2 else 'Не указано',
        'insurance': parts[3] if len(parts) > 3 else 'Не указано'
    }
    
    participants.append(participant)
    await state.update_data(participants=participants)
    
    if current < total:
        next_num = current + 1
        await state.update_data(current_participant=next_num)
        await message.answer(
            f"👤 Введите данные <b>участника №{next_num}</b>:\n"
            "Формат: ФИО, телефон, гос.номер, страховая компания",
            reply_markup=cancel_menu,
            parse_mode="HTML"
        )
    else:
        await state.update_data(photo_paths=[])
        await message.answer(
            "📸 Отправьте <b>минимум 3 фотографии</b> места ДТП:\n"
            "• Общий план с привязкой к местности\n"
            "• Повреждения каждого ТС\n"
            "• Номерные знаки и СТС\n\n"
            "Отправляйте фото по одному. Когда закончите, напишите 'Готово'",
            reply_markup=cancel_menu,
            parse_mode="HTML"
        )
        await state.set_state(AccidentStates.waiting_for_photos)

@router.message(AccidentStates.waiting_for_photos, F.photo)
async def process_accident_photos(message: Message, state: FSMContext):
    """Обработка фотографий ДТП"""
    photo: PhotoSize = message.photo[-1]
    
    # Генерируем уникальное имя файла
    filename = f"accident_{uuid.uuid4().hex}.jpg"
    filepath = Path("./data/photos") / filename
    
    # Скачиваем фото
    await message.bot.download(photo, destination=filepath)
    
    data = await state.get_data()
    photo_paths = data.get('photo_paths', [])
    photo_paths.append(str(filepath))
    await state.update_data(photo_paths=photo_paths)
    
    await message.answer(
        f"✅ Фото сохранено ({len(photo_paths)}/3+)\n"
        "Отправьте ещё фото или напишите 'Готово' для завершения:",
        reply_markup=cancel_menu
    )

@router.message(AccidentStates.waiting_for_photos, F.text.in_({"Готово", "готово", "✅ Готово"}))
async def finish_photos(message: Message, state: FSMContext):
    """Завершение загрузки фото"""
    data = await state.get_data()
    photo_paths = data.get('photo_paths', [])
    
    if len(photo_paths) < 3:
        await message.answer(
            f"⚠️ Требуется минимум 3 фотографии. Загружено: {len(photo_paths)}\n"
            "Отправьте ещё фото или напишите 'Готово' для завершения:",
            reply_markup=cancel_menu
        )
        return
    
    await message.answer(
        "📍 Отправьте геолокацию места ДТП (нажмите скрепку → геопозиция):",
        reply_markup=cancel_menu
    )
    await state.set_state(AccidentStates.waiting_for_location)

@router.message(AccidentStates.waiting_for_photos)
async def invalid_photo_command(message: Message):
    await message.answer(
        "Пожалуйста, отправьте фотографию или напишите 'Готово' для завершения:",
        reply_markup=cancel_menu
    )

@router.message(AccidentStates.waiting_for_location, F.location)
async def process_accident_location(message: Message, state: FSMContext):
    """Обработка геолокации ДТП"""
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    await state.update_data(latitude=latitude, longitude=longitude)
    await message.answer(
        "✏️ Опишите обстоятельства ДТП:\n"
        "• При каких обстоятельствах произошло (поворот, перестроение и т.д.)\n"
        "• Какие повреждения получены\n"
        "• Были ли пострадавшие (обязательно вызовите ГИБДД при наличии пострадавших!)",
        reply_markup=cancel_menu
    )
    await state.set_state(AccidentStates.waiting_for_description)

@router.message(AccidentStates.waiting_for_location)
async def invalid_location(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте именно геолокацию (нажмите скрепку → геопозиция).",
        reply_markup=cancel_menu
    )

@router.message(AccidentStates.waiting_for_description)
async def process_accident_description(message: Message, state: FSMContext):
    """Обработка описания ДТП"""
    description = sanitize_text(message.text, max_length=2000)
    await state.update_data(description=description)
    
    # Формируем подтверждение
    data = await state.get_data()
    participants = data.get('participants', [])
    
    confirmation = "📋 <b>Проверьте данные ДТП:</b>\n\n"
    confirmation += f"<b>Участники:</b> {len(participants)}\n"
    confirmation += f"<b>Фотографий:</b> {len(data.get('photo_paths', []))}\n"
    
    if data.get('latitude') and data.get('longitude'):
        confirmation += f"<b>Координаты:</b> {data['latitude']:.6f}, {data['longitude']:.6f}\n"
    
    confirmation += f"<b>Обстоятельства:</b> {description[:100]}...\n\n"
    confirmation += "✅ Подтвердить и сгенерировать европротокол?"
    
    await message.answer(
        confirmation,
        reply_markup=get_accident_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AccidentStates.confirming_accident)

@router.message(
    AccidentStates.confirming_accident,
    F.text.in_({"✅ Отправить", "✅ Да", "Да", "да", "✅ Отправить заявление"})
)
async def confirm_accident(message: Message, state: FSMContext):
    """Подтверждение и генерация европротокола"""
    data = await state.get_data()
    
    # Сохраняем в БД
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one()
        
        accident = AccidentReport(
            user_id=user.id,
            description=data['description'],
            participants=json.dumps(data['participants'], ensure_ascii=False),
            photo_paths=json.dumps(data.get('photo_paths', []), ensure_ascii=False),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            status="completed"
        )
        session.add(accident)
        await session.commit()
        await session.refresh(accident)
        
        # Генерируем документ
        accident_data = {
            'id': accident.id,
            'participants': data['participants'],
            'description': accident.description,
            'latitude': accident.latitude,
            'longitude': accident.longitude,
            'photo_paths': data.get('photo_paths', []),
            'created_at': accident.created_at
        }
        
        document_path = generate_accident_protocol(accident_data)
        accident.document_path = document_path
        await session.commit()
    
    # Отправляем документ
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
    await message.bot.send_document(
        chat_id=message.chat.id,
        document=FSInputFile(document_path),
        caption="✅ Ваше заявление успешно отправлено!...",
        parse_mode="HTML"
    )
    
    await message.answer(
        "Документы готовы! 📄\n"
        "Рекомендуем также:\n"
        "1. Обменяться контактами со всеми участниками\n"
        "2. Сфотографировать документы друг друга (ВУ, СТС, полис ОСАГО)\n"
        "3. Не покидать место ДТП до завершения оформления",
        reply_markup=main_menu
    )
    
    logger.info(f"Accident report #{accident.id} created by user {message.from_user.id}")
    await state.clear()

@router.message(AccidentStates.confirming_accident)
async def handle_accident_confirmation(message: Message):
    await message.answer(
        "Пожалуйста, подтвердите кнопкой '✅ Да' или отмените операцию кнопкой '❌ Отмена'",
        reply_markup=get_accident_confirm_keyboard()
    )
