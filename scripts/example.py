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
       pip install api_integration-<latest-tag-version>-py3-none-any.whl

    3. .env file with `APP_ENV=prod` and valid credentials must exist in the project root (./.env file)

    4. ./config/trusted_recipients.json must exist

    5. example.py must exist in ./scripts/example.py

Usage:
    # Windows CMD:
    python ./scripts/example.py

    # Windows PowerShell:
    python .\scripts\example.py

    # Or using the installed console script (if package is installed):
    run-api-integration
"""

from api_integration.pipeline import run_pipeline_with_lock

if __name__ == "__main__":
    run_pipeline_with_lock()
