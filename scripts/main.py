"""Локальный скрипт для ручного запуска и тестирования пайплайна"""

from api_integration.pipeline import run_pipeline_with_lock

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
SUBFOLDER: str | None = PASS_TEST_MESSAGE_ID_FOR_REPLY
# dry_run=True skips actual execution (safe mode, no side effects)
DRY_RUN: bool = False
# test_run=True forces execution (use with caution, may overwrite data)
TEST_RUN: bool = False

# In constants.py
# set IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS to skip adding suppliers (slow PUT)
# set IS_SEARCH_EXISTING_RFQ_BEFORE_POST to skip adding RFQ with same title


if __name__ == "__main__":
    from api_integration.constants import project_root
    from api_integration.config import get_settings

    settings = get_settings()
    print(f"APP_ENV={settings.APP_ENV}, project_root={project_root}")

    # Call locking wrapper around business logic pipeline
    run_pipeline_with_lock(
        subfolder=SUBFOLDER,
        dry_run=DRY_RUN,
        test_run=TEST_RUN,
    )
