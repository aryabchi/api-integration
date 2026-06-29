import sys
import time
from pathlib import Path
import requests
from pydantic import ValidationError

src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from constants import TEST_RFQ_CREATE_BOILERPLATE
from config import get_settings
from sevenrights.api.schemas.rfq import RfqCreateRequest
from sevenrights.api.utils import _print_validation_errors


def post_rfq(data: dict = None, timeout: int = 30) -> dict:

    settings = get_settings()

    payload_data = data if data is not None else TEST_RFQ_CREATE_BOILERPLATE

    try:
        model = RfqCreateRequest.model_validate(payload_data)
    except ValidationError as exc:
        _print_validation_errors(exc)
        return {
            "error": f"ValidationError: {exc.errors()}",
            "rfq_id": None,
        }

    body = model.model_dump(mode="json", exclude_none=True)

    url = f"{settings.SEVEN_RIGHTS_API_URL.rstrip('/')}/rfq"

    headers = {
        "Authorization": f"Bearer {settings.SEVEN_RIGHTS_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "rfq_id": None,
        }

    if response.status_code == 201:
        try:
            response_data = response.json()
        except ValueError:
            return {
                "error": "Invalid JSON in success response",
                "rfq_id": None,
            }

        rfq_id = response_data.get("id")
        if rfq_id is None:
            return {
                "error": "Missing 'id' in success response",
                "rfq_id": None,
            }

        return {
            "error": None,
            "rfq_id": rfq_id,
        }

    if response.status_code == 422:
        try:
            error_data = response.json()
        except ValueError:
            error_data = {}

        message = error_data.get("message", "Unknown validation error")
        errors = error_data.get("errors", {})

        return {
            "error": f"HTTP {response.status_code} ValidationError: {message} {errors}",
            "rfq_id": None,
        }

    return {
        "error": f"HTTP {response.status_code}: {response.text}",
        "rfq_id": None,
    }


if __name__ == "__main__":

    start_time = time.perf_counter()
    result = post_rfq(
        timeout=30,
        data={
            "title": "АВТО - Артем - Хабаровский край - 08.07.2026 - 01.09.2026",
            "finish_datetime": "2026-06-29T17:00:00",
            "requirements": "Уважаемые партнеры!\nПриглашаем Вас принять участие в тендере на перевозку Артем - Хабаровский край\n1 тур (3 дня) – светофор по целевому тарифу, общий список направлений\n2 тур (1 день) – рейтинг по тарифам перевозчика\nСрок оказания услуг: 08.07.2026-01.09.2026\nТарифы: принимаются в рублях\nВ случае неготовности подать предложение по направлению(-ям) просьба указывать ставку “0”.\nВАЖНО:\n1. Во второй тур/переторжку приглашаются только к/а, подавшие предложения в 1м туре! Если сталкиваетесь с проблемами при подаче предложений, просим связаться с ответственным лицом по тендеру до завершения приема предложений.\n2. Принятие ставок вне ЭТП запрещено.\nДополнительная информация к тендеру:\n\nЦелевой уровень OTIF по отгрузке - 89%. \nЦелевой уровень OTIF по доставке - 92%\nУслуги осуществляются по договору ТЭО (Форма СИБУР: ЕУФ_293)\nКритерии выбора: уровень сервиса, возможности компании по вывозу, стоимость, собственный автопарк.\nНовые перевозчики забирают не более 10% объема\nПо вопросам технической поддержки необходимо обращаться:\n∙ по телефонам: +7 (495) 222-37-00\n∙ E-mail: support@7rights.ru\nС уважением,\nкоманда СИБУР",
            "contract_start_date": "2026-07-08",
            "contract_end_date": "2026-09-01",
            "is_invite_link_enabled": True,  # Отправлять ссылку-приглашение по email
            "transport_type_ids": [1],  # "Авто, Полная FTL"
            "contact_ids": [
                118
            ],  # Тимофеева Анастасия невозможно установить контакты ни в contacts[], ни в contact_ids[]; контакт != пользователь; нет enpoint получения контактов
            "lot_template_id": 12993,  # каждый раз создается новый id
            # "user_access_ids": [
            #     108014,
            #     100511,
            #     108453,
            # ],  # создатель с "полный доступ", остальные с "только чтение"
            "user_access": [
                {"user_id": 108014, "access_type": 2},
                {"user_id": 100511, "access_type": 2},
                {"user_id": 108453, "access_type": 2},
            ],
            # Поставщики PUT /rfq/{id} - "access_type": "groups" + "supplier_group_ids": [29, 36]
            # "access_type": "groups",  # отваливается с таймаутом соединения => потерян rfq_id
            # "supplier_group_ids": [29, 36],  # Авто FTL СНГ; Авто FTL РФ
            "participant_access_type": 0,  # 0 - Прямой доступ, 1 - Доступ на опред условиях, 2 - Доступ после анкеты
            # "valutum_rate": 1, Какой-то курс перевода поле =1
            "freight_spend_of_event": 1,  # объем запроса предложений
            "freight_spend_currency_id": 1,  # выставляется в паре с объем запроса предложений
            # Обратная связь для поставщика:
            "type_view": 2,  #  0 - без обр связи, 1- рейтинг поставщика, 2- светофор, 3 - числовой рейтинг
            "traffic_light_type": 1,  # 0 - по рейтингу, 1 - по цене
            # нельзя настроить переключатель светофор на основе цены - лучшая, базовая, целевая (НЕТ ответа от 7Rights)
            "show_best_price": False,  # Обратная связь для поставщика - Не показывать лучшую цену (False), Отобразить (True)
            # Пролонгация:
            "prolongacia": False,  # Условия автоматической пролонгации = Запрещено
            # Повышение цен поставщиками в текущем туре
            "is_ban_on_price_increases_on_this_tour": True,  # Повышение цен поставщиками в текущем туре = Запрещено (false), Разрешено (true)
            # неясно какой параметр отвечает - Лучшая цена - отключено/включено??? Default - отключено
            "traffic_light_price_type": 2,
            "price_green_finish_percent": 93,
            "price_yellow_finish_percent": 85,
        },
    )
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(result)
    print(f"Request took {total_time:.6f} seconds to run")
