from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select, func
from src.database import Report, AccidentReport, User, get_db
from src.config import settings
from src.keyboards.main_menu import main_menu
from src.utils.logger import get_logger
logger = get_logger(__name__)
router = Router()

async def show_statistics(message: Message):
    """Показать статистику администратору"""
    # Проверка прав администратора
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer(
            "❌ У вас нет прав доступа к админ-панели.\n"
            "Обратитесь к организатору проекта для получения доступа."
        )
        return
    
    async with get_db() as session:
        # Статистика по жалобам
        total_reports = await session.scalar(select(func.count(Report.id)))
        new_reports = await session.scalar(
            select(func.count(Report.id)).where(Report.status == "new")
        )
        resolved_reports = await session.scalar(
            select(func.count(Report.id)).where(Report.status == "resolved")
        )
        
        # Статистика по ДТП
        total_accidents = await session.scalar(select(func.count(AccidentReport.id)))
        
        # Статистика по пользователям
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(func.distinct(User.id))).where(
                User.id.in_(
                    select(Report.user_id).union(select(AccidentReport.user_id))
                )
            )
        )
    
    stats_text = (
        "📊 <b>Статистика системы RoadDoc</b>\n\n"
        f"👤 Всего пользователей: {total_users}\n"
        f"📈 Активных пользователей: {active_users}\n\n"
        f"📝 Всего жалоб: {total_reports}\n"
        f"🆕 Новых жалоб: {new_reports}\n"
        f"✅ Решённых проблем: {resolved_reports}\n\n"
        f"🚗 Оформлено ДТП: {total_accidents}\n\n"
        "<i>Данные обновлены в реальном времени</i>"
    )
    
    await message.answer(stats_text, reply_markup=main_menu, parse_mode="HTML")
    logger.info(f"Admin {message.from_user.id} viewed statistics")
