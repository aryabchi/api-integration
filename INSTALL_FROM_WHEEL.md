# Установка из wheel-файла (без публикации в PyPI)

Этот гайд описывает установку пакета `api_integration` из локального wheel-файла на целевом сервере/рабочей станции.

## Предварительные требования

- Python >= 3.11
- pip (обновленный до последней версии)

## Шаги установки

### 1. Передача wheel-файла

Скопируйте файл `dist/api_integration-0.1.0-py3-none-any.whl` на целевую машину.

### 2. Установка зависимостей

На этом шаге происходит установка пакета `api_integration` и его runtime-зависимостей (`pydantic`, `requests`, `openpyxl`, и т.д.) в текущее Python-окружение.

#### 2.1 Обновите pip

```bash
pip install --upgrade pip
```

Это гарантирует, что pip сможет корректно:
- разрешать зависимости из wheel
- работать с современными форматами метаданных
- корректно обрабатывать версии пакетов

#### 2.2 Установите пакет из wheel

```bash
pip install dist/api_integration-0.1.0-py3-none-any.whl
```

**Что происходит при установке:**
- pip читает метаданные из `api_integration-0.1.0.dist-info/METADATA`
- автоматически скачивает и устанавливает зависимости, указанные в `dependencies` (pydantic==2.11.10, requests==2.33.0, openpyxl==3.1.5, pydantic-settings==2.10.1)
- копирует модули `api_integration` в `site-packages` текущего окружения
- регистрирует пакет в окружении, делая его доступным через `import api_integration`

#### 2.3 Вариации установки

**Если нужно установить конкретную версию Python/окружение:**
```bash
# Для Python 3.11
py -3.11 -m pip install dist/api_integration-0.1.0-py3-none-any.whl

# В конкретное виртуальное окружение
.\venv\Scripts\pip install dist/api_integration-0.1.0-py3-none-any.whl
```

**Если нужен editable-режим (для разработки):**
```bash
pip install -e .
```
В этом режиме пакет остается связанным с исходным кодом через символическую ссылку, и изменения в `src/` сразу доступны без переустановки.

#### 2.4 Проверка установки

После установки проверьте, что пакет доступен:

```bash
python -c "import api_integration; print(api_integration.__file__)"
```

Ожидаемый вывод — путь к `api_integration/__init__.py` внутри `site-packages`.

#### 2.5 Если pip не находит wheel

Убедитесь, что:
- вы находитесь в директории, содержащей `dist/` (обычно это корень проекта `api-integration`)
- имя файла совпадает с тем, что в директории `dist/`
- используется актуальный pip (`pip --version`)

### 3. Проверка установки

```bash
python -c "import api_integration; print('OK')"
```

### 4. Настройка конфигурации

```bash
cp .env.example .env
```

Заполните переменные в `.env`:
- `MAILBOX_NAME` / `MAILBOX_APP_PASSWORD`
- `IMAP_SERVER` / `IMAP_PORT`
- `SMTP_SERVER` / `SMTP_PORT`
- `SEVEN_RIGHTS_API_BASE_URL` / `SEVEN_RIGHTS_API_VERSION` / `SEVEN_RIGHTS_API_KEY`

Создайте `config/trusted_recipients.json` со списком доверенных email-адресов.

### 5. Запуск

```bash
python ./scripts/main.py
```

## Примечания

- Пакет устанавливается в `site-packages` целиком и не требует исходного кода.
- При обновлении пакета сначала удалите старую версию (`pip uninstall api_integration`) и установите новый wheel.
- Для разработки используйте editable-режим: `pip install -e .`