import logging
from pydantic import ValidationError

# (no absolute imports needed; package-relative)

logger = logging.getLogger(__name__)


def _normalize_error(error) -> list[str]:
    """Normalize error field to list[str] format."""
    if error is None:
        return []
    if isinstance(error, str):
        return [error]
    if isinstance(error, list):
        return error
    return [str(error)]


def _print_validation_errors(exc: ValidationError) -> None:
    logger.info("VALIDATION FAILED")
    logger.info("=" * 80)

    for idx, error in enumerate(exc.errors(), start=1):
        field = ".".join(str(x) for x in error["loc"])
        message = error["msg"]
        error_type = error["type"]

        logger.info(f"[{idx}] Field : {field}")
        logger.info(f"    Type  : {error_type}")
        logger.info(f"    Error : {message}")

    logger.info("=" * 80)
