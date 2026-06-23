"""Module with app-specific constants"""

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent

# Local directory to save attachments
DOWNLOADS_DIR = f"{project_root}/downloads"

# The subject template to search for (IMAP does a substring match)
SUBJECT_TEMPLATE = "*"

# Full mail search pattern
# IMAP search syntax. SUBJECT does a substring match. HAS_ATTACHMENT doesn't work
IMAP_MAIL_SEARCH_TEMPLATE = (
    f'(SUBJECT "{SUBJECT_TEMPLATE}" HEADER "Content-Type" "multipart/mixed")'
)

# Desired email attachment extension

ALLOWED_ATTACHMENT_FILE_EXTENSIONS = (".xlsx", ".xls", ".xlsm", ".xlsb")
