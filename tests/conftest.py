import os

import pytest

# Obfuscated dummy values used only during tests.
# Real secrets must NOT be committed — keep them in .env or CI secrets.
TEST_ENV = {
    "MAILBOX_NAME": "test@example.com",
    "MAILBOX_APP_PASSWORD": "test-app-password",
    "IMAP_SERVER": "imap.example.com",
    "IMAP_PORT": "993",
    "SMTP_SERVER": "smtp.example.com",
    "SMTP_PORT": "465",
    "SEVEN_RIGHTS_API_BASE_URL": "https://example.com/",
    "SEVEN_RIGHTS_API_VERSION": "api/v1/",
    "SEVEN_RIGHTS_API_KEY": "test-api-key",
    "SEVEN_RIGHTS_API_AWAIT_TIMEOUT": "30",
    "APP_ENV": "dev",
    "MAIL_SERVER": "INTERNET",
    "LOG_LEVEL": "WARNING",
    "EXCHANGE_USERNAME": "DOMAIN\\user",
    "EXCHANGE_PASSWORD": "test-password",
    "EXCHANGE_SERVER": "mail.example.local",
    "PRIMARY_SMTP_ADDRESS": "user@example.com",
}


def pytest_load_initial_conftests(early_config, parser, args):
    """Inject obfuscated settings before any test module is imported.

    This makes `Settings()` validation succeed even when no `.env` is present
    (e.g. in GitHub Actions CI).
    """
    os.environ.update(TEST_ENV)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Reset lru_cache so each test starts fresh."""
    from api_integration.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
