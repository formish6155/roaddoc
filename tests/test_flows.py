import asyncio
import datetime
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, Update, User as TgUser
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import src.database as database
from src.bot.middlewares import FirstContactMiddleware
from src.config import settings
from src.handlers import router
from src.states.report_states import ReportStates

# Роутер можно подключить только к одному Dispatcher, поэтому он общий; состояние сбрасывается в asyncSetUp
DP = Dispatcher(storage=MemoryStorage())
DP.message.middleware(FirstContactMiddleware())
DP.include_router(router)


class TestBotFlows(unittest.IsolatedAsyncioTestCase):
    """Сообщения проходят через настоящий Dispatcher, middleware и обработчики; БД и файлы во временной папке"""

    async def asyncSetUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        engine = create_async_engine(f"sqlite+aiosqlite:///{self.tmp / 'test.db'}")
        self.patches = [
            patch.object(database, "engine", engine),
            patch.object(database, "AsyncSessionLocal", sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)),
            patch.object(settings, "DOCS_DIR", self.tmp),
            patch.object(settings, "ADMIN_IDS", []),
            patch.object(Message, "answer", AsyncMock()),
            patch.object(Bot, "send_chat_action", AsyncMock()),
            patch.object(Bot, "send_document", AsyncMock()),
        ]
        for p in self.patches:
            p.start()
        await database.create_db_and_tables()
        self.bot = Bot("123:abc")
        self.dp = DP
        self.key = StorageKey(bot_id=self.bot.id, chat_id=1, user_id=1)
        await self.dp.storage.set_state(self.key, None)
        await self.dp.storage.set_data(self.key, {})
        self.update_id = 0

    async def asyncTearDown(self):
        await self.bot.session.close()
        await database.engine.dispose()
        for p in reversed(self.patches):
            p.stop()

    def message(self, text):
        self.update_id += 1
        return Update(update_id=self.update_id, message=Message(
            message_id=self.update_id, date=datetime.datetime.now(), text=text,
            chat=Chat(id=1, type="private"), from_user=TgUser(id=1, is_bot=False, first_name="Тест"),
        ))

    async def count(self, model):
        async with database.get_db() as session:
            return await session.scalar(select(func.count()).select_from(model))

    async def test_first_messages_at_once_register_user_once(self):
        await asyncio.gather(*(self.dp.feed_update(self.bot, self.message("/start")) for _ in range(3)))
        self.assertEqual(await self.count(database.User), 1)

    async def test_double_tap_on_confirm_creates_one_report(self):
        await self.dp.feed_update(self.bot, self.message("/start"))
        await self.dp.storage.set_state(self.key, ReportStates.confirming_report)
        await self.dp.storage.set_data(self.key, {"problem_type": "Яма / выбоина", "description": "x" * 500})
        await asyncio.gather(*(self.dp.feed_update(self.bot, self.message("✅ Сформировать заявление")) for _ in range(2)))
        self.assertEqual(await self.count(database.Report), 1)
        self.assertEqual(len(list(self.tmp.glob("report_*.pdf"))), 1)

    async def test_cancel_deletes_downloaded_photo(self):
        photo = self.tmp / "report_abandoned.jpg"
        photo.write_bytes(b"jpg")
        await self.dp.storage.set_state(self.key, ReportStates.waiting_for_location_method)
        await self.dp.storage.set_data(self.key, {"photo_path": str(photo)})
        await self.dp.feed_update(self.bot, self.message("❌ Отмена"))
        self.assertFalse(photo.exists())
        self.assertIsNone(await self.dp.storage.get_state(self.key))


if __name__ == "__main__":
    unittest.main()
