"""Модуль проверки адресата письма на списку доверенных получателей"""

import json
import os

from api_integration.constants import TRUSTED_RECIPIENTS_FILE


def is_trusted_email(email: str, filename: str = TRUSTED_RECIPIENTS_FILE) -> bool:
    """
    Checks if an email is in the trusted local JSON list.

    Args:
        email (str): The email address to verify.
        filename (str): The path to the JSON file.

    Returns:
        bool: True if the email is trusted, False otherwise.
    """
    # Clean the input to prevent false negatives from spaces or casing
    email_clean = email.strip().lower()

    # Return False immediately if the file does not exist
    if not os.path.exists(filename):
        print(f"Warning: Configuration file '{filename}' not found.")
        return False

    try:
        with open(filename, "r", encoding="utf-8") as file:
            trusted_set = {str(e).strip().lower() for e in json.load(file)}
            return email_clean in trusted_set

    except json.JSONDecodeError:
        print(f"Error: '{filename}' contains invalid JSON formatting.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


if __name__ == "__main__":
    # Test cases
    test_email = "ADMIN@example.com "

    if is_trusted_email(test_email):
        print("Access granted.")
    else:
        print("Access denied.")
