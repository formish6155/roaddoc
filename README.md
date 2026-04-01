# RoadDoc

Telegram-бот для:
- подачи обращений о дорожных проблемах;
- оформления ДТП по европротоколу;
- просмотра базовой статистики (для администраторов).

## Требования

- Python 3.12+
- Telegram Bot Token от `@BotFather`

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Создайте `.env` в корне проекта:

```env
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789,987654321
DATABASE_URL=sqlite+aiosqlite:///./data/database.db
LOG_LEVEL=INFO
```

Запуск:

```bash
python3 -m src.main
```

## Проверки

Синтаксическая проверка:

```bash
python3 -m compileall src tests
```

Тесты, не требующие внешней инфраструктуры:

```bash
python3 -m unittest -q tests.test_services tests.test_handlers
```
