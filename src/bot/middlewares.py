# src/bot/middlewares.py
from aiogram.types import Message, TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
                username = event.from_user.username
                full_name = f"{event.from_user.first_name} {event.from_user.last_name or ''}".strip()

                if not user:
                    # Регистрируем пользователя и пропускаем сообщение дальше.
                    # Это сохраняет первый апдейт (например /start), а не "съедает" его.
                    new_user = User(
                        telegram_id=event.from_user.id,
                        username=username,
                        full_name=full_name
                    )
                    session.add(new_user)
                    try:
                        await session.commit()
                    except IntegrityError:
                        # Параллельное сообщение того же пользователя уже создало запись
                        await session.rollback()
                elif (user.username, user.full_name) != (username, full_name):
                    # Админы создаются при старте с заглушками вместо имени; заменяем на реальные данные
                    user.username = username
                    user.full_name = full_name
                    await session.commit()
        
        return await handler(event, data)
