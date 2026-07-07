"""End-to-end processing pipeline"""

import sys
import msvcrt
import logging

from api_integration.config import get_settings
from api_integration.mail.imap.fetch import fetch_mail as fetch_imap_mail
from api_integration.mail.ews.fetch import fetch_mail as fetch_ews_mail
from api_integration.mail.compose import generate_replies
from api_integration.mail.smtp.send import send_replies
from api_integration.sevenrights.rfq.create import create_rfqs
from api_integration.excel.convert import process_attachments_wrapper
from api_integration.constants import (
    project_root,
    LOCK_FILE,
)
from api_integration.logger import setup_logging

# Инициализируем именованный логгер для этого модуля
logger = logging.getLogger(__name__)


def run_pipeline(
    subfolder: str | None = None,
    dry_run: bool = False,
    test_run: bool = False,
) -> None:
    """Pure processing pipeline (just business logic).

    Args:
        subfolder: Target message ID or subfolder name to process.
        dry_run: If True, skip actual write/send operations (safe mode).
        test_run: If True, bypass conditional checks and overwrite historical results.
    """

    settings = get_settings()
    mailbox = settings.MAILBOX_NAME
    password = settings.MAILBOX_APP_PASSWORD

    # Print pipeline configuration
    logger.info("=== Mail processing pipeline ===")
    logger.info(
        f"Configuration: APP_ENV={settings.APP_ENV}, project_root={project_root}, subfolder={subfolder}, dry_run={dry_run}, test_run={test_run}"
    )

    # 1. fetch emails, save attachments
    logger.info("Step 1: Fetching emails and saving attachments")
    if settings.MAIL_SERVER == "CORPORATE":
        logger.info("Using Exchange EWS fetcher")
        fetch_ews_mail()
    else:
        logger.info("Using Internet IMAP fetcher")
        fetch_imap_mail()
    logger.info("Step 1 completed: Fetch mail")

    # 2. process attachments
    logger.info("Step 2: Processing attachments")
    process_attachments_wrapper(
        dry_run=dry_run,
        test_run=test_run,
        subfolder=subfolder,
    )
    logger.info("Step 2 completed: Process attachments")

    # 3. create RFQs
    logger.info("Step 3: Creating RFQs")
    create_rfqs(
        dry_run=dry_run,
        test_run=test_run,
        subfolder=subfolder,
        timeout=settings.SEVEN_RIGHTS_API_AWAIT_TIMEOUT,
    )
    logger.info("Step 3 completed: Create RFQs")

    # 4. generate replies
    logger.info("Step 4: Generating replies")
    generate_replies(
        dry_run=dry_run,
        test_run=test_run,
        subfolder=subfolder,
    )
    logger.info("Step 4 completed: Generate replies")

    # 5. send replies
    logger.info("Step 5: Sending replies")
    send_replies(
        subfolder=subfolder,
        dry_run=dry_run,
        test_run=test_run,
    )
    logger.info("Step 5 completed: Send replies")

    logger.info("=== Pipeline execution completed ===")


def run_pipeline_with_lock(
    subfolder: str | None = None,
    dry_run: bool = False,
    test_run: bool = False,
) -> None:
    """App entry point. Wrapper around business logic pipeline
    Win обертка управления блокировкой (Предотвращает параллельный запуск).
    Именно ее вызываем из планировщика задач Windows (см .toml) и из /scripts
    """
    try:
        # ПЕРВЫМ ДЕЛОМ инициализируем логи.
        # Если Pydantic упадет на этом этапе из-за кривого .env,
        # ошибка вызовется ниже в блоке except ValidationError.
        setup_logging()
    except Exception as log_err:
        # Запасной вариант на случай, если даже логгер не смог создаться
        print(f"Критическая ошибка инициализации логгера: {log_err}", file=sys.stderr)
        sys.exit(1)

    # Open lock file in Append + Read mode
    LOCK_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )  # Гарантируем наличие родительской папки для lock-файла перед открытием
    lock_fp = LOCK_FILE.open("a+")

    try:
        # Trying to lock 1 byte of file w/o awaiting  (LK_NBLCK)
        msvcrt.locking(lock_fp.fileno(), msvcrt.LK_NBLCK, 1)
    except (IOError, OSError):
        # If file is locked by concurrent process -> exit(0) silently
        logger.warning(
            f"[LOCK] {LOCK_FILE} is already locked by another process. Exiting."
        )
        # lock_fp.close()
        sys.exit(0)

    try:
        # Если блокировка успешна -> запускаем пайплайн
        run_pipeline(
            subfolder=subfolder,
            dry_run=dry_run,
            test_run=test_run,
        )
    except Exception as e:
        # КРИТИЧЕСКИ ВАЖНО ДЛЯ WINDOWS SCHEDULER:
        # Перехватываем абсолютно любую непредвиденную ошибку бизнес-логики
        # и записываем её полный Traceback (стек вызовов) в файл лога.
        logger.exception(f"Критический сбой при выполнении конвейера: {e}")
        sys.exit(1)
    finally:
        # Гарантированно освобождаем блокировку и закрываем файл
        try:
            lock_fp.seek(0)
            msvcrt.locking(lock_fp.fileno(), msvcrt.LK_UNLCK, 1)
        except (IOError, OSError):
            pass
        lock_fp.close()
