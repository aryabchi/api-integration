"""Module with app-specific constants"""

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent

# Flag to skip calling put_rfq_supplier_group_ids (PUT call may slow pipeline down)
# True - skip, False - execute
IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS = False

# Flag to do/skip RFQ search (by title) before creation attempt
# True for production, False for testing
IS_SEARCH_EXISTING_RFQ_BEFORE_POST = False

# Default lot_template_id (unless brand new created first)
# 12993 -> Копия ТЗ Самсунг Артем перезакуп Хабаровский край 19.06.2026.xlsx
# 13200 -> "ТЗ Малино-Смоленск.xlsx"

# None -> MUST-BE value as template_id is not know apriori
RFQ_DEFAULT_LOT_TEMPLATE_ID: int | None = None


# Default organizer user_access_ids
# TODO: rm UNUSED
RFQ_DEFAULT_ORGANIZER_USER_ID: int = 108014

# Local directory with json samples for API requests
SAMPLES_DIR = f"{project_root}/samples"

# Local directory for imcoming emails, attachments and interim precessing flags
DOWNLOADS_DIR = f"{project_root}/downloads"

# Local directory for user-level json configurations
CONFIG_DIR = f"{project_root}/config"

# Config dir for trusted recipients
TRUSTED_RECIPIENTS_FILE = f"{CONFIG_DIR}/trusted_recipients.json"

# The subject template to search for (IMAP does a substring match)
SUBJECT_TEMPLATE = "*"

# Full mail search pattern
# IMAP search syntax. SUBJECT does a substring match. HAS_ATTACHMENT doesn't work
IMAP_MAIL_SEARCH_TEMPLATE = (
    f'(SUBJECT "{SUBJECT_TEMPLATE}" HEADER "Content-Type" "multipart/mixed")'
)

# Accepted email attachment extensions supported by openpyxl, e.g. .xlsx, .xlsm, but NOT .xls
ALLOWED_ATTACHMENT_FILE_EXTENSIONS = (".xlsx",)

# Required patterns in attachemnt file names
ALLOWED_ATTACHMENT_LOT_TEMPLATE_TERMS = ("тз",)
ALLOWED_ATTACHMENT_RFQ_TEMPLATE_TERMS = ("шаблон", "запрос", "тендер", "параметры")

# Name of the placeholder file that indicates a reply message body has been composed
REPLY_BODY_MARKER = "reply.txt"

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
    "Здравствуйте,<br>"
    "В ответ на Ваше письмо {subject_line} от {date}.<br><br>"
    "Мы автоматически создали RFQ: {message} <br><br>"
    "{extra_on_success}"
    "<br><br>"
    "---- Original message ----<br>{body_excerpt}<br>"
    "------------------------------------<br><br>"
    "С наилучшими пожеланиями,<br>"
    "Агент Коля<br>"
)

ERROR_REPLY_TEMPLATE = (
    "Здравствуйте,<br>"
    "В ответ на Ваше письмо {subject_line} от {date}.<br><br>"
    "Нам не удалось автоматически создать RFQ <br><br>"
    "Описание причины:<br>"
    "{message}"
    "<br><br>"
    "---- Original message ----<br>{body_excerpt}<br>"
    "------------------------------------<br><br>"
    "С наилучшими пожеланиями,<br>"
    "Агент Коля<br>"
)

PARTIAL_SUCCESS_REPLY_TEMPLATE = (
    "Здравствуйте,<br>"
    "В ответ на Ваше письмо {subject_line} от {date}.<br><br>"
    "Мы автоматически создали RFQ: {message} <br><br>"
    "{extra_on_success}"
    "<br><br>"
    "Предупреждение:<br>"
    "{warning}"
    "<br><br>"
    "---- Original message ----<br>{body_excerpt}<br>"
    "------------------------------------<br><br>"
    "С наилучшими пожеланиями,<br>"
    "Агент Коля<br>"
)

# TODO: rm after testing, USED somewhere
# Minimal required RFQ info for create
TEST_RFQ_CREATE_BOILERPLATE = {
    "title": "Тестовая закупка транспортных услуг",
    "finish_datetime": "2026-07-01T18:00:00Z",
}

# Possible mapping of Excel field name "Наим поля в UI"
# (from Шаблон запроса создания тендера v1.3/TENDER)
# to RfqCreateRequest properties
EXCEL_TO_RFQ_MAPPING = {
    # Core Identification & Text
    "Название": "title",
    # "Площадка": "name_for_human", # skip
    # "Направление": "name_for_human", # skip
    "Информация для поставщика услуг": "requirements",
    # Dates & Timelines
    "Дата и время окончания": "finish_datetime",
    # "Дата публикации": "published_at",
    "Срок действия ТКП от": "contract_start_date",
    "Срок действия ТКП до": "contract_end_date",
    # Access & Participants
    "Прямой доступ": "participant_access_type",
    "Пригласить поставщиков": "supplier_group_ids",
    "Полный доступ": "user_access",
    "Отправлять ссылку-приглашение по email": "is_invite_link_enabled",
    "Контактное лицо": "contact_ids",
    # Transport & Lots
    "Вид транспорта": "transport_type_ids",
    "Объем запроса предложений": "freight_spend_of_event",
    # Visibility & Traffic Light Settings
    "Показывать лучшую цену": "show_best_price",
    # "Лучшая цена": "zzz", # skip комбинация {type_view = 1, show_best_price (true/false)}
    "Светофор на основе": "traffic_light_type",
    "Показывать светофор на основе цены": "traffic_light_price_type",
    "Зеленый сигнал светофора от": "price_green_finish_percent",  # lower bound only
    "Желтый сигнал светофора от": "price_yellow_finish_percent",  # lower bound only
    # "Красный сигнал светофора от": "", # unused
    # Prolongation & Rules
    "Автоматическая пролонгация": "prolongacia",
    # "Время пролонгации": "max_date_prolongacia", # skip
    "Обратная связь для поставщиков": "type_view",
    "Повышение цен поставщиками": "is_ban_on_price_increases_on_this_tour",
}


# Mappings of excel RFQ template values "Значение по умолчанию"/"Значение" to 7rights API IDs
EXCEL_TO_RFQ_VALUES_MAPPING = {
    "is_invite_link_enabled": {
        "Да": True,
        "да": True,
        "Нет": False,
        "нет": False,
    },
    "transport_type_ids": {
        "Авто, Полная FTL": [1],
    },
    "participant_access_type": {
        "Да": 0,
        "да": 0,
        "Нет": 1,
        "нет": 1,
    },  # 0 = Прямой доступ, 1 = Доступ на опред условиях, 2 = Доступ после анкеты
    #  Сопутствующие поля:
    # participant_access_type = 1 → gate_requirement (обязательно), is_need_transporter_file (опционально)
    # participant_access_type = 2 → questionnaire_form_id (обязательно); справочник: GET /rfq/questionnaire-forms
    "contact_ids": {
        "Тимофеева Анастасия": [118],
        "Тимофеева Анастасия Николаевна": [118],
    },
    # "user_access_ids": {
    #     "Тимофеева Анастасия Николаевна": [108014],
    #     "Слепян Анна Дмитриевна": [100511],
    #     "Цуриков Константин Эдуардович": [108453],
    #     "Набока Михаил Викторович": [114835],
    # },  # obsolete: создатель с "полный доступ", остальные с "только чтение"
    "user_access": {
        "Тимофеева Анастасия Николаевна": [{"user_id": 108014, "access_type": 2}],
        "Слепян Анна Дмитриевна": [{"user_id": 100511, "access_type": 2}],
        "Цуриков Константин Эдуардович": [{"user_id": 108453, "access_type": 2}],
        "Набока Михаил Викторович": [{"user_id": 114835, "access_type": 2}],
    },
    # Поставщики -> PUT /rfq/{id} - "access_type": "groups" + "supplier_group_ids": [29, 36]
    "supplier_group_ids": {
        "Авто FTL СНГ": [29],
        "Авто FTL РФ": [36],
    },  # Авто FTL СНГ; Авто FTL РФ
    # "valutum_rate": 1, Какой-то курс перевода поле =1
    # Обратная связь для поставщика:
    "type_view": {
        "Запрос данных, без обратной связи": 0,
        "Обратная связь в виде числового рейтинга": 1,
        "Обратная связь в виде светофора": 2,
        "Обратная связь в виде числового рейтинга от наибольшей цены": 3,
    },  #  0 = без обр связи, 1 = рейтинг поставщика, 2 = светофор, 3 = числовой рейтинг
    "traffic_light_type": {
        "светофор по целевому тарифу": 1,
        "светофору по рейтингу": 0,
    },  # 0 = по рейтингу, 1 = по цене
    # при traffic_light_type=1: price_green_finish_percent, price_yellow_finish_percent
    # при traffic_light_type=0: rating_green_finish_value, rating_yellow_finish_value
    "traffic_light_price_type": {
        "Целевая цена": 2,
        "Базовая цена": 1,
        "Лучшая цена": 0,
    },
    "show_best_price": {
        "Не показывать лучшую цену": False,
        "Отобразить лучшую цену": True,
    },  # Обратная связь для поставщика - Не показывать лучшую цену = False, Отобразить = True
    "prolongacia": {
        "Запрещено": False,
        "Разрешено, при переходе из красной/желтой зоны в зеленую": True,
        "Разрешено, при выходе из красной в желтую/зеленую зону": True,
    },  # Условия автоматической пролонгации = Запрещено
    "is_ban_on_price_increases_on_this_tour": {
        "Разрешено": False,
        "Запрещено": True,
        "Запрещено понижать": False,
    },  # Повышение цен поставщиками в текущем туре - Запрещено = true, Разрешено = false
    # неясно какой параметр отвечает - вероятно type_view = 1 + show_best_price
    # "zzz": {
    #     "Включено": "x",
    #     "Отключено": "y",
    # },
}

# Hardcoded mappings from RfqCreateRequest properties to constant values
RFQ_TO_DEFAULTS_MAPPING = {
    "access_type": "groups",  # paired with supplier_group_ids
    "freight_spend_currency_id": 1,  # Валюта RUB: freight_spend_currency_id: 1 идет вместе с freight_spend_of_event
    # "is_for_all": False,  # optional, тендер создаётся как черновик без приглашённых поставщиков
}
