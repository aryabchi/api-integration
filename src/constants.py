"""Module with app-specific constants"""

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent


# Local directory with json samples for API requests
SAMPLES_DIR = f"{project_root}/samples"

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
# Set empty to allow all types of attachments, populate if save only desired e.g. xlsx
ALLOWED_ATTACHMENT_FILE_EXTENSIONS = (".xlsx", ".xls", ".xlsm", ".xlsb")

# Name of the placeholder file that indicates a reply has been successfully sent
REPLY_SENT_MARKER = "reply_sent.txt"

# Name of the placeholder file that indicates **result** of RFQ create API call
RFQ_INFO_MARKER = "rfq_info.json"

# Name of the placeholder file that contains fields extracted from emailed **Excel attachments**
RFQ_EXCEL_MARKER = "rfq_excel.json"

# Draft RFQ link
RFQ_DRAFT_URL = "https://lk.7rights.ru/admin/newRfq/{rfq_id}"

# Reply email templates
SUCCESS_REPLY_TEMPLATE = (
    "Здравствуйте,\n"
    "В ответ на Ваше письмо {subject_line} от {date}.\n\n"
    "Мы автоматически создали RFQ: {message}. "
    "\n\n"
    "---- Original message ----\n{body_excerpt}\n"
    "------------------------------------\n\n"
    "С наилучшими пожеланиями,\n"
    "Агент Коля\n"
)

ERROR_REPLY_TEMPLATE = (
    "Здравствуйте,\n"
    "В ответ на Ваше письмо {subject_line} от {date}.\n\n"
    "Нам не удалось автоматически создать RFQ.\n\n"
    "Описание причины:\n"
    "{message}"
    "\n\n"
    "---- Original message ----\n{body_excerpt}\n"
    "------------------------------------\n\n"
    "С наилучшими пожеланиями,\n"
    "Агент Коля\n"
)


TEST_RFQ_CREATE_BOILERPLATE = {
    "title": "Тестовая закупка транспортных услуг",
    "finish_datetime": "2026-07-01T18:00:00Z",
}

# Possible mapping of Excel field name "Наим поля в UI"
# (from Шаблон запроса создания тендера v1.3/TENDER)
# to RfqCreateRequest properties
EXCEL_TO_RFQ_MAPPING = {
    # Core Identification & Text
    "Название": "title",  # Ok string
    # "Площадка": "name_for_human",
    # "Направление": "name_for_human",
    "Информация для поставщика услуг": "requirements",  # Ok string
    # Dates & Timelines
    "Дата и время окончания": "finish_datetime",  # Ok string
    # "Дата публикации": "late_submission_datetime",
    "Срок действия ТКП от": "contract_start_date",  # Ok string
    "Срок действия ТКП до": "contract_end_date",  # Ok string
    # Access & Participants
    "Прямой доступ": "access_type",  # ? enum: ["all", "selected", "groups"]
    "Пригласить поставщиков": "supplier_company_ids",  # Ok array
    "Полный доступ": "user_access_ids",  # Ok array
    # "Отправлять ссылку-приглашение по email": "supplier_emails", # ?
    "Контактное лицо": "contacts",  # Ok array
    # Transport & Lots
    "Вид транспорта": "transport_type_ids",  # Ok array
    # "Объем запроса предложений": "income_id",  # ?
    # Visibility & Traffic Light Settings
    # "Показывать лучшую цену": "type_view",
    # "Лучшая цена": "type_view", # ?
    # "Светофор на основе": "traffic_light_type", # ?
    # "Показывать светофор на основе цены": "traffic_light_type",
    # "Зеленый сигнал светофора от": "traffic_light_type", # no match
    # "Желтый сигнал светофора от": "traffic_light_type", # no match
    # "Красный сигнал светофора от": "traffic_light_type", # no match
    # Prolongation & Rules
    "Автоматическая пролонгация": "prolongacia",  # Ok boolean
    # "Время пролонгации": "max_date_prolongacia",  # ?
    "Обратная связь для поставщиков": "type_view",  # ? enum: [1, 2, 3], 1 — рейтинг, 2 — лучшая цена, 3 — светофор
    # "Повышение цен поставщиками": "can_questions",  # ?
}


# Hardcoded mappings from RfqCreateRequest properties to constant values
RFQ_TO_DEFAULTS_MAPPING = {
    "lot_template_id": 12993,  # ID шаблона
    "supplier_company_ids": [
        1014358,
        1013339,
        1013160,
        1012739,
        1012407,
    ],  # sampled from Авто FTL СНГ; Авто FTL РФ
    "user_access_ids": [
        108014,  # Тимофеева Анастасия Николаевна;
        100511,  # Слепян Анна Дмитриевна;
        108453,  # Цуриков Константин Эдуардович;
        114835,  # Набока Михаил Викторович
    ],
    "access_type": "all",
    "type_view": 3,  # ?
    "prolongacia": False,
    "transport_type_ids": [1],  # ?
    "contacts": [108014],  # Тимофеева Анастасия
}
