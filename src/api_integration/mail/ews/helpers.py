from typing import Optional

from exchangelib import Credentials, Account, Configuration, DELEGATE
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib.errors import (
    UnauthorizedError,
    ErrorNonExistentMailbox,
    ErrorImpersonationDenied,
    ErrorAccessDenied,
    ErrorInternalServerError,
    ErrorServerBusy,
    TransportError,
)

from api_integration.config import get_settings

logger = __import__("logging").getLogger(__name__)
settings = get_settings()


def create_exchange_account(mailbox: str, password: str) -> Optional[Account]:
    """Create and verify Exchange account connection.

    Returns Account on success, None on failure.
    """
    try:
        logger.info(f"Connecting to Exchange server: {settings.EXCHANGE_SERVER}...")

        credentials = Credentials(
            username=settings.EXCHANGE_USERNAME,
            password=password,
        )

        # Подменяем стандартный класс сессии в exchangelib на игнорирующий TLS validation errors
        BaseProtocol.HTTP_ADAPTER_CLS.session_class = NoVerifyHTTPAdapter
        BaseProtocol.HTTP_ADAPTER_CLS.DEFAULT_TIMEOUT = 30

        config = Configuration(
            server=settings.EXCHANGE_SERVER,
            credentials=credentials,
        )

        account = Account(
            primary_smtp_address=mailbox,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
        logger.info("Configuration initialized. Checking real network connection...")
        # РЕАЛЬНЫЙ ТЕСТ: Запрашиваем версию сервера по сети.
        # Это принудительно инициирует веб-сессию и проверит credentials
        server_version = account.protocol.version

        logger.info(
            f"Successfully connected to Exchange Server! "
            f"Server version: {server_version.build}. "
            f"Access to mailbox {mailbox} succeeds."
        )
        return account

    except UnauthorizedError as e:
        logger.error(
            f"Exchange Authentication Failed: Invalid username or password. {e}"
        )
    except ErrorNonExistentMailbox as e:
        logger.error(f"Exchange Mailbox Not Found: {mailbox}. {e}")
    except ErrorImpersonationDenied as e:
        logger.error(f"Exchange Impersonation Denied: {e}")
    except ErrorAccessDenied as e:
        logger.error(f"Exchange Access Denied: {e}")
    except ErrorServerBusy as e:
        logger.error(f"Exchange Server Busy: {e}")
    except (ErrorInternalServerError, TransportError) as e:
        logger.error(
            f"Exchange Internal Server Error or Mailbox Store Unavailable: {e}"
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.debug(__import__("traceback").format_exc())

    return None
