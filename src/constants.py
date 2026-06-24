"""Module with app-specific constants"""

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent

# Local directory to save attachments
DOWNLOADS_DIR = f"{project_root}/downloads"

# Config dir for trusted recipients
TRUSTED_RECIPIENTS_FILE = f"{project_root}/config/trusted_recipients.json"

# The subject template to search for (IMAP does a substring match)
SUBJECT_TEMPLATE = "*"

# Full mail search pattern
# IMAP search syntax. SUBJECT does a substring match. HAS_ATTACHMENT doesn't work
IMAP_MAIL_SEARCH_TEMPLATE = (
    f'(SUBJECT "{SUBJECT_TEMPLATE}" HEADER "Content-Type" "multipart/mixed")'
)

# Desired email attachment extension
ALLOWED_ATTACHMENT_FILE_EXTENSIONS = (".xlsx", ".xls", ".xlsm", ".xlsb")

# Name of the placeholder file that indicates a reply has been successfully sent
REPLY_SENT_MARKER = "reply_sent.txt"

# Draft RFQ link
RFQ_DRAFT_LINK = r"https://7rights.ru"

# Reply email template
DEFAULT_REPLY_TEMPLATE = (
    "Здравствуйте, {sender_name},\n\n"
    "В ответ на Ваше письмо {subject_line} от {date}.\n\n"
    "Мы создали RFQ {rfq_link}. "
    "\n\n"
    "---- Original message ----\n{body_excerpt}\n"
    "------------------------------------\n\n"
    "С наилучшими пожеланиями,\n"
    "Агент Коля\n"
)
