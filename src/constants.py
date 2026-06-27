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

# Required patterns in attachemnts
ALLOWED_ATTACHMENT_LOT_TEMPLATE_TERMS = ("тз",)
ALLOWED_ATTACHMENT_RFQ_TEMPLATE_TERMS = ("шаблон", "запрос", "тендер")

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

# Flag to skip very SLOW put_rfq_supplier_group_ids PUT
# TODO: add to pipleine if adding suppliers really slows it down
IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS = False

# Minimal required RFQ info for create (testing)
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
    # "Площадка": "name_for_human",
    # "Направление": "name_for_human",
    "Информация для поставщика услуг": "requirements",
    # Dates & Timelines
    "Дата и время окончания": "finish_datetime",
    # "Дата публикации": "published_at",
    "Срок действия ТКП от": "contract_start_date",
    "Срок действия ТКП до": "contract_end_date",
    # Access & Participants
    "Прямой доступ": "participant_access_type",
    "Пригласить поставщиков": "supplier_group_ids",
    "Полный доступ": "user_access_ids",
    "Отправлять ссылку-приглашение по email": "is_invite_link_enabled",
    "Контактное лицо": "contact_ids",
    # Transport & Lots
    "Вид транспорта": "transport_type_ids",
    "Объем запроса предложений": "freight_spend_of_event",
    # Visibility & Traffic Light Settings
    "Показывать лучшую цену": "show_best_price",
    # "Лучшая цена": "zzz", # ??? Default = отключено
    "Светофор на основе": "traffic_light_type",
    # "Показывать светофор на основе цены": "xxx", # ???
    # "Зеленый сигнал светофора от": "", # ???
    # "Желтый сигнал светофора от": "", # ???
    # "Красный сигнал светофора от": "", # ???
    # Prolongation & Rules
    "Автоматическая пролонгация": "prolongacia",
    # "Время пролонгации": "max_date_prolongacia",  # ?
    "Обратная связь для поставщиков": "type_view",
    "Повышение цен поставщиками": "is_ban_on_price_increases_on_this_tour",
}


# Default organizer user_access_ids
RFQ_DEFAULT_ORGANIZER_USER_ID: int = 108014

# Default lot_template_id:
RFQ_DEFAULT_LOT_TEMPLATE_ID: int = 12993


# Mappings of excel RFQ template values "Значение по умолчанию"/"Значение" to 7rights API valid IDs
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
        "Да": 0,  # 0 - Прямой доступ, 1 - Доступ на опред условиях, 2 - Доступ после анкеты
        "да": 0,
        "Нет": 1,
        "нет": 1,
    },
    "contact_ids": {
        "Тимофеева Анастасия": [118],
        "Тимофеева Анастасия Николаевна": [118],
    },
    "user_access_ids": {
        "Тимофеева Анастасия Николаевна": [108014],
        "Слепян Анна Дмитриевна": [100511],
        "Цуриков Константин Эдуардович": [108453],
        "Набока Михаил Викторович": [114835],
    },  # создатель с "полный доступ", остальные с "только чтение"
    # Поставщики PUT /rfq/{id} - "access_type": "groups" + "supplier_group_ids": [29, 36]
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
    },  #  0 - без обр связи, 1- рейтинг поставщика, 2- светофор, 3 - числовой рейтинг
    "traffic_light_type": {
        "светофор по целевому тарифу": 1,
        "светофору по рейтингу": 0,
    },  # 0 - по рейтингу, 1 - по цене
    # нельзя настроить переключатель светофор на основе цены - лучшая, базовая, целевая (НЕТ ответа от 7Rights)
    # "xxx": {
    #     "Целевая цена": "x",
    #     "Базовая цена": "y",
    #     "Лучшая цена": "z",
    # },
    "show_best_price": {
        "Не показывать лучшую цену": False,
        "Отобразить лучшую цену": True,
    },  # Обратная связь для поставщика - Не показывать лучшую цену (False), Отобразить (True)
    "prolongacia": {
        "Запрещено": False,
        "Разрешено, при переходе из красной/желтой зоны в зеленую": True,
        "Разрешено, при выходе из красной в желтую/зеленую зону": True,
    },  # Условия автоматической пролонгации = Запрещено
    # Повышение цен поставщиками в текущем туре
    "is_ban_on_price_increases_on_this_tour": {
        "Разрешено": False,
        "Запрещено": True,
        "Запрещено понижать": False,
    },  # Повышение цен поставщиками в текущем туре = Запрещено (true), Разрешено (false)
    # неясно какой параметр отвечает - Лучшая цена - отключено/включено???
    # "zzz": {
    #     "Включено": "x",
    #     "Отключено": "y",
    # },
}

# Hardcoded mappings from RfqCreateRequest properties to constant values
RFQ_TO_DEFAULTS_MAPPING = {
    "lot_template_id": RFQ_DEFAULT_LOT_TEMPLATE_ID,  # ID шаблона, пересоздается
    "access_type": "groups",  # отваливается с таймаутом соединения
    "freight_spend_currency_id": 1,  # выставляется в паре с freight_spend_of_event
}
