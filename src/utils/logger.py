import logging
import sys
from structlog import configure, processors, stdlib
from pathlib import Path
from src.config import settings

def setup_logging():
    """Настройка структурированного логирования"""
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
    
    # Настройка structlog
    configure(
        processors=[
            stdlib.filter_by_level,
            stdlib.add_logger_name,
            stdlib.add_log_level,
            stdlib.PositionalArgumentsFormatter(),
            processors.TimeStamper(fmt="iso"),
            processors.StackInfoRenderer(),
            processors.format_exc_info,
            processors.UnicodeDecoder(),
            stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=stdlib.LoggerFactory(),
        wrapper_class=stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    """Получение логгера с заданным именем"""
    return logging.getLogger(name)
