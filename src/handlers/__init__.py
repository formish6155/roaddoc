# src/handlers/__init__.py
from aiogram import Router
from .start import router as start_router
from .reports import router as reports_router
from .accidents import router as accidents_router
from .admin import router as admin_router

router = Router(name="main_router")

# Подключаем все роутеры
router.include_router(start_router)
router.include_router(reports_router)
router.include_router(accidents_router)
router.include_router(admin_router)

__all__ = ["router"]
