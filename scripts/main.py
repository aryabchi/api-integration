"""End-to-end processing pipeline"""

import sys
import msvcrt

from api_integration.config import get_settings
from api_integration.mail.fetch import fetch_mail
from api_integration.mail.compose import generate_replies
from api_integration.mail.send import send_replies
from api_integration.sevenrights.rfq.create import create_rfqs
from api_integration.excel.convert import process_attachments_wrapper
from api_integration.constants import LOCK_FILE

# ============ Example subfolders for testing ============
# Use only ONE of these per run - select the appropriate test message ID
PASS_TEST_MESSAGE_ID_FOR_REPLY = (
    "26671782368771@mail.yandex.ru"  # trusted recipient, valid excel attachments
)
FAIL_TEST_MESSAGE_ID_FOR_REPLY = (
    "87311782287117@mail.yandex.ru"  # trusted recipient, insufficient attachments
)


# ============================================================
# Common parameters for the entire pipeline (used in all steps)
# ============================================================
# WARNING: test_run=True bypasses all conditional checks and tries to execute
# actions potentially overwriting historical results. Use it:
# - With caution
# - For debugging
# - In conjunction with subfolder argument

# Target message-ID (subfolder name) for processing specific email thread
# None runs pipeline for all email threads
SUBFOLDER: str | None = None
# dry_run=True skips actual execution (safe mode, no side effects)
DRY_RUN: bool = False
# test_run=True forces execution (use with caution, may overwrite data)
TEST_RUN: bool = False

# In constants.py
# set IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS to skip adding suppliers (slow PUT)
# set IS_SEARCH_EXISTING_RFQ_BEFORE_POST to skip adding RFQ with same title


def main(
    subfolder: str | None = SUBFOLDER,
    dry_run: bool = DRY_RUN,
    test_run: bool = TEST_RUN,
) -> None:
    """Execute the mail processing pipeline.
    TODO: Move into package, import here

    Args:
        subfolder: Target message ID or subfolder name to process.
        dry_run: If True, skip actual write/send operations (safe mode).
        test_run: If True, bypass conditional checks and overwrite historical results.
    """

    settings = get_settings()
    mailbox = settings.MAILBOX_NAME
    password = settings.MAILBOX_APP_PASSWORD

    # Print pipeline configuration
    print("=== Mail processing pipeline ===")
    print(f"subfolder={subfolder}, dry_run={dry_run}, test_run={test_run}")

    # 1. get emails, save attachments
    print("\n>>> Step 1: Fetching emails and saving attachments")
    fetch_mail(
        imap_server=settings.IMAP_SERVER,
        imap_port=settings.IMAP_PORT,
        mailbox=mailbox,
        password=password,
    )
    print("<<< Step 1 completed: Fetch mail")

    # 2. process attachments
    print("\n>>> Step 2: Processing attachments")
    process_attachments_wrapper(
        dry_run=dry_run,
        test_run=test_run,
        subfolder=subfolder,
    )
    print("<<< Step 2 completed: Process attachments")

    # 3. create RFQs
    print("\n>>> Step 3: Creating RFQs")
    create_rfqs(
        dry_run=dry_run,
        test_run=test_run,
        subfolder=subfolder,
        timeout=settings.SEVEN_RIGHTS_API_AWAIT_TIMEOUT,
    )
    print("<<< Step 3 completed: Create RFQs")

    # 4. generate replies
    print("\n>>> Step 4: Generating replies")
    generate_replies(
        dry_run=dry_run,
        test_run=test_run,
        subfolder=subfolder,
    )
    print("<<< Step 4 completed: Generate replies")

    # 5. send replies
    print("\n>>> Step 5: Sending replies")
    send_replies(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        sender_email=mailbox,
        sender_password=password,
        subfolder=subfolder,
        dry_run=dry_run,
        test_run=test_run,
    )
    print("<<< Step 5 completed: Send replies")

    print("\n=== Pipeline execution completed ===")


if __name__ == "__main__":
    # !!! First of ALL - open lock file in Append + Read mode
    lock_fp = LOCK_FILE.open("a+")
    try:
        # Trying to lock 1 byte of file w/o awaiting  (LK_NBLCK)
        msvcrt.locking(lock_fp.fileno(), msvcrt.LK_NBLCK, 1)
    except (IOError, OSError):
        # If file is locked by concurrent process -> exit(0) silently
        print(f"{LOCK_FILE} locked")
        sys.exit(0)

    try:
        # If locking succeeds -> launch main pipeline
        main(
            subfolder=SUBFOLDER,
            dry_run=DRY_RUN,
            test_run=TEST_RUN,
        )
    finally:
        # Release locking unconditionally and close file before exit
        try:
            lock_fp.seek(0)
            msvcrt.locking(lock_fp.fileno(), msvcrt.LK_UNLCK, 1)
        except (IOError, OSError):
            pass
        lock_fp.close()
