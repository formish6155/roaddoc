import logging
import sys
from pathlib import Path
from src.config import settings

def setup_logging():
    """Логи в файл logs/roaddoc.log и в консоль"""
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    # Очистка существующих обработчиков
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Базовый обработчик для файлов
    file_handler = logging.FileHandler(log_dir / "roaddoc.log")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        handlers=[file_handler, console_handler],
        force=True
    )

def get_logger(name: str):
    """Получение логгера с заданным именем"""
    return logging.getLogger(name)
