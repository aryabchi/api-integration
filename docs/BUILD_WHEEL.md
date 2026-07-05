# Сборка wheel-пакета (Build Wheel Guide)

Этот гайд описывает процесс сборки дистрибутивных артефактов (wheel и sdist) для проекта `api_integration`.

## Предварительные требования

- Python >= 3.11
- pip (обновленный до последней версии)
- Действительный `pyproject.toml` в корне проекта

## Шаги сборки

### 1. Установка инструмента сборки

Виртуальное окружение не требуется для сборки, но если вы хотите изолировать build-инструменты:

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install --upgrade pip
```

Установите `build` (PEP 517 фронтенд):

```bash
pip install build
```

> **Примечание:** `setuptools` и `wheel` будут автоматически установлены во временной изолированной среде при сборке. Вам не нужно устанавливать их в текущее окружение.

### 2. Сборка пакетов

Запустите команду из корня проекта (`api-integration/`):

```bash
cd api-integration
python -m build
```

**Что делает команда:**
1. Создает временную изолированную среду
2. Устанавливает туда `setuptools>=64` и `wheel` из `[build-system]`
3. Читает `pyproject.toml` для определения метаданных и пакетов
4. Собирает:
   - **wheel** — `dist/api_integration-0.1.0-py3-none-any.whl`
   - **sdist** — `dist/api_integration-0.1.0.tar.gz`

### 3. Результаты сборки

После успешной сборки в папке `dist/` появятся:

| Файл | Назначение |
|------|-----------|
| `api_integration-0.1.0-py3-none-any.whl` | Wheel-пакет для установки через `pip install` |
| `api_integration-0.1.0.tar.gz` | Source distribution (исходный код + метаданные) |

### 4. Проверка wheel

Убедитесь, что wheel содержит все необходимые модули:

#### 4.1 Просмотр содержимого

```bash
python -m zipfile -l dist/api_integration-0.1.0-py3-none-any.whl
```

Ожидаемое содержимое должно включать:
- `api_integration/__init__.py`
- `api_integration/config.py`
- `api_integration/constants.py`
- `api_integration/excel/*`
- `api_integration/mail/*`
- `api_integration/sevenrights/**`

#### 4.2 Проверка метаданных

```bash
python -m zipfile -e dist/api_integration-0.1.0-py3-none-any.whl .\tmp_wheel
cat .\tmp_wheel\api_integration-0.1.0.dist-info\METADATA
```

Или через `pkginfo`:

```bash
pip install pkginfo
python -c "import pkginfo; w = pkginfo.Wheel('dist/api_integration-0.1.0-py3-none-any.whl'); print(w.name, w.version)"
```

### 5. Очистка временных файлов

По желанию удалите артефакты сборки:

```bash
# Удалить временные файлы сборки
rmdir /s /q build
rmdir /s /q src\api_integration.egg-info

# Или используйте cleanup (Windows PowerShell)
Remove-Item -Recurse -Force build, src\api_integration.egg-info
```

> **Важно:** Не удаляйте папку `dist/` — там хранятся готовые wheel-файлы для распространения.

## Типичные проблемы

### Проблема: ModuleNotFoundError при сборке

Убедитесь, что:
- `src/api_integration/` содержит `__init__.py`
- В `pyproject.toml` секция `[tool.setuptools.packages.find]` указывает `where = ["src"]`
- Импорты внутри модулей корректны (относительно корня пакета)

### Проблема: wheel не содержит sub-packages

Если sub-packages (`excel`, `mail`, `sevenrights`) не попадают в wheel:

```bash
# Проверьте, что pyproject.toml корректно настроен:
# [tool.setuptools.packages.find]
# where = ["src"]

# Если auto-discovery не работает, перечислите пакеты явно:
# [tool.setuptools]
# packages = ["api_integration", "api_integration.excel", "api_integration.mail", "api_integration.sevenrights"]
```

### Проблема: зависимости не устанавливаются при `pip install wheel`

Проверьте, что в `pyproject.toml` секция `[project]` содержит `dependencies` в формате PEP 508.

## Сравнение wheel и sdist

| Тип | Плюсы | Минусы |
|-----|-------|--------|
| **wheel** | Быстрая установка, без компиляции, предсказуемость | Больший размер, не包含 исходный код |
| **sdist** | Содержит исходный код, универсальность | Медленная установка, требует build工具 |

Для CI/CD или распространения внутри команды обычно достаточно wheel.

## Скрипт сборки (опционально)

Создайте `build.bat` в корне проекта:

```bat
@echo off
cd /d "%~dp0api-integration"
python -m build
pause
```

Или `build.ps1`:

```powershell
Set-Location "$PSScriptRoot\api-integration"
python -m build
```

## Related docs

- `INSTALL_FROM_WHEEL.md` — инструкция по установке готового wheel
- `README.md` — общая документация проекта


## Комментарии 

Если у пользователя нет прав на установку (pip install) на целевой машине

```
pip download . --destination-directory dist\dependencies
# dist/* --> target host 
```