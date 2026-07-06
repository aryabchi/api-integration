# src/api_integration/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from api_integration.config import get_settings
from api_integration.constants import project_root


def setup_logging():
    """Настраивает сквозное логирование (консоль + файл с ротацией 5МБ x 10 файлов)."""
    if logging.getLogger().hasHandlers():
        return

    settings = get_settings()

    log_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # 1. Поток в консоль (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # 2. Поток в файл на диске с автоматической ротацией
    log_file_path = project_root / settings.LOG_FILE_NAME
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=settings.LOG_MAX_BYTES,  # Сюда прилетит 5_242_880
        backupCount=settings.LOG_BACKUP_COUNT,  # Сюда прилетит 10
        encoding="utf-8",
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
