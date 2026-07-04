import sys
import logging
from api_integration.config import get_settings
from pythonjsonlogger import jsonlogger


def setup_logging():
    """
    Configures centralized logging for the application.

    In dev mode:
    - Outputs to console in a human-readable format
    - Log level: DEBUG

    In prod mode:
    - Outputs to console in JSON format (for log aggregation)
    - Log level: INFO
    """
    settings = get_settings()

    # Create a logger for the application
    logger = logging.getLogger("api_integration")
    logger.setLevel(logging.DEBUG if settings.is_dev else logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if settings.is_dev:
        # Dev: human-readable format for debugging
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Prod: JSON format for aggregation (ELK, CloudWatch, etc.)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
            json_ensure_ascii=False,
        )

    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.is_dev else logging.INFO)
    logger.addHandler(console_handler)

    # Disable propagation to avoid duplicating logs in the root logger
    logger.propagate = False

    return logger


# global logger instance
logger = setup_logging()
