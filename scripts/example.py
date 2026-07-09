"""
Minimal script to launch the API integration pipeline.

Prerequisites:
    1. Virtual environment must be created and activated:
       # Create (CMD):
       python -m venv .venv

       # Create (PowerShell):
       python -m venv .venv

       # Activate (CMD):
       .venv\Scripts\activate.bat

       # Activate (PowerShell):
       .\.venv\Scripts\Activate.ps1

    2. Latest .whl must be installed IN THAT virtual env
       # dependencies from Internet
       pip install api_integration-<latest-tag-version>-py3-none-any.whl
       # OR dependencies from local dir (no Internet)
       pip install --no-index --find-links=.\dist --find-links=.\dist\dependencies api_integration
       # if installing new version run first
       pip uninstall api_integration -y

    3. .env file with `APP_ENV=prod` and valid credentials must exist in the project root (./.env file)
       `MAIL_SERVER=INTERNET` connects to Yandex mail servers, may fail from inside SIBUR net
       `MAIL_SERVER=CORPORATE` connects to MS Exchange (in autodiscover mode), needs valid `EXCHANGE_` credentials, may fail

    4. ./config/trusted_recipients.json must exist, fix mail addresses for testing

    5. example.py must exist in ./scripts/example.py

Usage:
    # Windows CMD:
    python ./scripts/example.py

    # Windows PowerShell:
    python .\scripts\example.py

    # Or without virtual env pre-activation:
    .\.venv\Scripts\python .\scripts\example.py

    # Or using the installed console .exe script:
    run-api-integration
"""

from api_integration.pipeline import run_pipeline_with_lock

if __name__ == "__main__":
    run_pipeline_with_lock()
