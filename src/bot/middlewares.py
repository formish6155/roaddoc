# src/bot/middlewares.py
from aiogram.types import Message, TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from sqlalchemy import select
from ..database import User, get_db

class FirstContactMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict
    ):
        if isinstance(event, Message) and event.from_user:
            async with get_db() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == event.from_user.id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    # Регистрируем пользователя и пропускаем сообщение дальше.
                    # Это сохраняет первый апдейт (например /start), а не "съедает" его.
                    new_user = User(
                        telegram_id=event.from_user.id,
                        username=event.from_user.username,
                        full_name=f"{event.from_user.first_name} {event.from_user.last_name or ''}".strip()
                    )
                    session.add(new_user)
                    await session.commit()
        
        return await handler(event, data)
