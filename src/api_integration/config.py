"""Configuration settings and secrets"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from pydantic import (
    Field,
    AnyHttpUrl,
)


def get_env_file_path() -> Path:
    """
    Динамически определяет путь к .env файлу.
    """
    # 1. Проверяем структуру разработки (рядом с папкой src)
    dev_root = Path(__file__).resolve().parent.parent.parent
    if (dev_root / "src").exists() and (dev_root / ".env").exists():
        return dev_root / ".env"

    # 2. Для продакшена (Windows Scheduler) используем текущую рабочую директорию.
    # В планировщике Windows обязательно должно быть заполнено поле "Рабочая папка" (Start in).
    return Path(".env").resolve()


class Settings(BaseSettings):
    """
    App settings from env vars
    """

    model_config = SettingsConfigDict(
        # Передаем динамический путь к файлу
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    MAILBOX_NAME: str = Field(description="Имя почтового ящика автологиста")
    MAILBOX_APP_PASSWORD: str = Field(
        description="Секретный app-пароль почтового ящика для скрипта"
    )
    IMAP_SERVER: str = Field(default="imap.yandex.ru", description="IMAP сервер")
    IMAP_PORT: int = Field(default=993, description="IMAP порт")

    SMTP_SERVER: str = Field(default="smtp.yandex.ru", description="SMTP сервер")
    SMTP_PORT: int = Field(default=465, description="SMTP порт")

    SEVEN_RIGHTS_API_BASE_URL: AnyHttpUrl = Field(description="Базовый URL API 7rights")
    SEVEN_RIGHTS_API_VERSION: str = Field(description="Суффикс с версией API 7rights")
    SEVEN_RIGHTS_API_KEY: str = Field(description="API ключ 7rights")
    SEVEN_RIGHTS_API_AWAIT_TIMEOUT: int = Field(
        description="Таймаут ожидания ответа от API 7rights, сек"
    )
    APP_ENV: str = Field(
        default="dev",
        pattern="^(dev|prod)$",
        description="Режим запуска (критически влиется на project_root -> поиск .env и расположение рабочих директорий)",
    )
    # поля для логирования
    LOG_LEVEL: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    LOG_FILE_NAME: str = Field(
        default="pipeline.log", description="Имя файла для логов"
    )

    @property
    def SEVEN_RIGHTS_API_URL(self) -> str:
        """Полный URL для вызова модели в Ollama."""
        return f"{str(self.SEVEN_RIGHTS_API_BASE_URL).rstrip('/')}/{self.SEVEN_RIGHTS_API_VERSION.rstrip('/')}"


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached setting
    """
    return Settings()
