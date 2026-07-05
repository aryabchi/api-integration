# src/api_integration/logger.py
import logging
import sys
from api_integration.config import get_settings
from api_integration.constants import project_root


def setup_logging():
    """Настраивает сквозное логирование для всего приложения."""
    # Проверяем, настроен ли уже логгер, чтобы избежать дублирования
    if logging.getLogger().hasHandlers():
        return

    settings = get_settings()

    # Формат логов: Время [Уровень] [Имя_Модуля]: Сообщение
    log_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # 1. Обработчик для вывода в консоль (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # 2. Обработчик для записи в файл (всегда создается в корне project_root)
    log_file_path = project_root / settings.LOG_FILE_NAME

    # Гарантируем, что папка существует (актуально, если путь кастомный)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
