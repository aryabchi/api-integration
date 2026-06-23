"""Configuration settings and secrets"""

from functools import lru_cache
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from pydantic import Field


class Settings(BaseSettings):
    """
    App settings from env vars
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    MAILBOX_NAME: str = Field(description="Имя почтового ящика")
    MAILBOX_APP_PASSWORD: str = Field(
        default=None, description="Пассворд почтового ящика для скрипта"
    )
    IMAP_SERVER: str = Field(default="imap.yandex.ru", description="IMAP server")
    IMAP_PORT: int = Field(default=993, description="IMAP port")


@lru_cache
def get_settings() -> Settings:
    """
    Returns caches setting
    """
    return Settings()
