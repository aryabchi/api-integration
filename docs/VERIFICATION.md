# Руководство по верификации собранного пакета (.whl)


## Шаг 1(a). Сборка пакета Wheel (локально)
Выполните сборку артефакта из корня вашего репозитория разработки:
```bash
pip install build
python -m build
```
*Результат:* Создание директории `dist/` с файлом пакета (например, `api_integration-<version-tag>-py3-none-any.whl`).

## Шаг 1(b). Альтернативно сборке (GitHub)
Скачайте сборку с **последним** тэгом с [GitHub](https://github.com/aryabchi/api-integration/tags) Downloads


## Шаг 2. Изоляция среды пользователя
Создайте чистую рабочую папку в любой другой точке диска (имитация окружения Windows Task Scheduler):
```bash
cd C:\
mkdir TestUserEnv
cd TestUserEnv
```

## Шаг 3. Развертывание виртуального окружения
Создайте и активируйте изолированную среду Python:
```bash
python -m venv .venv
# Для PowerShell:
.\.venv\Scripts\Activate.ps1
# Для CMD:
.\.venv\Scripts\activate.bat
```
*Результат:* В начале строки терминала появится префикс (`.venv`), подтверждающий, что вы внутри чистой среды

## Шаг 4. Подготовка пользовательских настроек
Создайте конфигурационный файл `.env` прямо в папке `C:\TestUserEnv`, скопируйте из `.env.example` и проверьте.
**НЕ ЗАБУДЬТЕ** установить `APP_ENV=prod`

```
# === Internet mail settings (не используются при MAIL_SERVER=CORPORATE) 
MAILBOX_NAME=your-email@example.com
MAILBOX_APP_PASSWORD=your-app-password
SEVEN_RIGHTS_API_KEY=your-api-key

# === RFQ Pipeline flags ===
# Пропустить медленный PUT запрос для поставщиков
IS_SKIP_PUT_RFQ_SUPPLIER_GROUP_IDS=false
# Искать существующий RFQ по названию перед созданием (true для продакшен)
IS_SEARCH_EXISTING_RFQ_BEFORE_POST=true

# === Режим запуска: prod ===
APP_ENV=prod # !!! 

# === Mail server type (INTERNET=Yandex IMAP/SMTP, CORPORATE=MS Exchange EWS) ===
# На основе этого принимается решение, по каким протоколам происходит получение/отправка почты
MAIL_SERVER=CORPORATE 

# === Режим логирования: DEBUG|INFO|WARNING|ERROR|CRITICAL ===
LOG_LEVEL=DEBUG

# === MS Exchange settings для MAIL_SERVER=CORPORATE  ===
EXCHANGE_USERNAME=CORP\dedicated_accont_with_mailbox
EXCHANGE_PASSWORD=dedicated_account_with_mailbox_password
EXCHANGE_SERVER=mail.sibur.local # correct MAPI server, defauld port 443
# Указываем адрес ящика, который нужно проверять и от имени которого слать ответы:
PRIMARY_SMTP_ADDRESS=dedicated_account_mailbox@sibur.ru
```

Создайте `config\trusted_recipients.json`
```
[
    "somebody@somewhere.ru"
]
```

## Шаг 5(a). Установка из собранного пакета (С подтягиванием зависимостей из PyPI через интернет)
Установите собранный на Шаге 1 `.whl` файл. Замените путь на фактический путь к вашему репозиторию:
```bash
pip install C:\full_path_to\api_integration-<version-tag>-py3-none-any.whl
```
Уствновка более новой версии должна автоматически удалить предыдущую
```
pip install api_integration-<version-next-tag>-py3-none-any.whl
```
*Результат:* Автоматическая загрузка внешних зависимостей (`pydantic`, `openpyxl`, ...) и генерация исполняемого файла `run-api-integration.exe` в подпапке `.venv\Scripts\`.

## Шаг 5(b). Оффлайн-установка пакета и зависимостей (Без интернета и прав админа)
Поскольку у пользователя может не быть прав на глобальную установку или доступ к интернету заблокирован, устанавливаем локально внутри `.venv` из заранее скачанных пакетов.

Выполните команду установки, указав путь к папке `dist`, _которую передал разработчик_, выполнив `pip download . -d ./dist/dependencies`:
```bash
pip install --no-index --find-links=C:\путь_к_папке_dist\dependencies\ --find-links=C:\путь_к_папке_dist\ api_integration
```

При повторной установке той же версии whl
```
pip install --no-index --find-links=D:\путь_к_папке_dist\dist --find-links=D:\путь_к_папке_dist\dist\dependencies api_integration
```

При обновлении версии whl
```bash
pip install --upgrade --no-index --find-links=D:\путь_к_папке_dist\dist --find-links=D:\путь_к_папке_dist\dist\dependencies api_integration
```

Удаление пакета
```bash
pip uninstall api_integration -y 
```

* `--no-index` — принудительно запрещает `pip` ходить в интернет на сайт PyPI.
* `--find-links=...` — указывает локальные папки, где лежат заготовленные `.whl` файлы зависимостей и вашей библиотеки.
* `api_integration` — имя вашего пакета из `pyproject.toml`, который `pip` найдет в указанных папках и установит.
* `--upgrade` — заставляет pip удалить старую версию библиотеки, удалить старый .exe файл и установить новые.

*Результат:* Все библиотеки (`pydantic` и др.) и ваша точка входа `run-api-integration.exe` успешно развернуты внутри `C:\TestUserEnv\.venv\`

## Шаг 6(a). Имитация запуска Windows Scheduler
Убедитесь, что 
- терминал находится в контексте директории `C:\TestUserEnv`,
- виртуальное окружение активировано (`.venv`)

Выполните зарегистрированную точку входа:
```bash
run-api-integration
```

Альтернативно, если исполняемый файл не исполняется, выполните как запуск модуля
```bash
python -m api_integration.pipeline
```

## Шаг 6(b). Настройка реального запуска в Windows Task Scheduler

Для регламентного запуска скрипта в планировщике задач Windows не требуется вызывать скрипты активации окружения. Планировщик должен запускать сгенерированный `.exe` файл напрямую из папки виртуального окружения, принудительно выставляя рабочую директорию.

В окне создания действия **«Запуск программы» (Start a program)** заполните поля следующим образом:

1. **Программа или сценарий (Program/script):**
   Укажите абсолютный путь к исполняемому файлу вашей точки входа внутри `.venv`:
   ```text
   C:\TestUserEnv\.venv\Scripts\run-api-integration.exe
   ```

2. **Аргументы (Add arguments):**
   Оставьте поле пустым (параметры `subfolder=None`, `dry_run=False`, `test_run=False` применятся автоматически по умолчанию).

3. **Рабочая папка (Start in) — КРИТИЧЕСКИ ВАЖНО:**
   Укажите абсолютный путь к папке, где лежит файл `.env` и где должны создаваться пользовательские файлы:
   ```text
   C:\TestUserEnv
   ```

### Критерии успешной проверки:
1. **Режим запуска:** Логи в stdout отображают 
```bash
=== Mail processing pipeline ===
Configuration: APP_ENV=prod, ...
...
=== Pipeline execution completed ===
```
2. **Артефакты:** Внутри `C:\TestUserEnv\` автоматически сгенерированы:
   - Папка `downloads/` (видимая для пользователя, ее наполнение зависит от содержимого почтового ящика `PRIMARY_SMTP_ADDRESS`)
   - Файл блокировки процесса `.lock`
   - Файл лога `.log`
3. **Параллельный запуск:** Повторный вызов команды `run-api-integration` (в соседнем терминале) завершается мгновенно и без ошибок


### Комментарии

1. В Windows 11 при попытке активировать окружение командой `.\.venv\Scripts\Activate.ps1` вы можете получить красную ошибку: «...выполнение скриптов отключено в этой системе».

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Это разрешит запуск скриптов только для текущего окна терминала без изменения глобальной безопасности ОС. (При реальном запуске через Windows Scheduler этой проблемы нет, так как мы вызываем .exe напрямую, минуя .ps1

2. Если у пользователя нет прав на установку (pip install) на целевой машине

См. Шаг 5(b)