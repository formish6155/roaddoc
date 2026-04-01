# src/main.py
import asyncio
import sys
from pathlib import Path

# Настройка путей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.config import settings
from src.database import create_db_and_tables
from src.handlers import router
from src.bot.middlewares import FirstContactMiddleware
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    # Создаём структуру папок
    settings.create_directories()
    
    # Создаём БД и таблицы
    await create_db_and_tables()
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Bot started successfully: @{bot_info.username} (ID: {bot_info.id})")
    print(f"\n✅ RoadDoc бот запущен!")
    print(f"   Имя: @{bot_info.username}")
    print(f"   Для тестирования напишите боту: https://t.me/{bot_info.username}")
    print(f"   Админ-панель доступна для ID: {settings.ADMIN_IDS}")
    print(f"   Логи сохраняются в: ./logs/roaddoc.log\n")

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("Bot shutting down...")
    print("\n🛑 RoadDoc бот остановлен")

async def main():
    """Точка входа в приложение"""
    # Валидация токена
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("BOT_TOKEN не установлен в .env файле!")
        print("\n❌ ОШИБКА: Необходимо указать BOT_TOKEN в файле .env")
        print("   1. Скопируйте .env.example в .env")
        print("   2. Получите токен у @BotFather в Telegram")
        print("   3. Вставьте токен в .env файл\n")
        return
    
    # Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация middleware для автоматического приветствия
    dp.message.middleware(FirstContactMiddleware())
    
    # Подключение роутеров
    dp.include_router(router)
    
    # Регистрация обработчиков жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск поллинга
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Bot crashed with error: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Critical error during startup: {e}")
        sys.exit(1)
