from pydantic import ValidationError

# (no absolute imports needed; package-relative)


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
    print("\nVALIDATION FAILED")
    print("=" * 80)

    for idx, error in enumerate(exc.errors(), start=1):
        field = ".".join(str(x) for x in error["loc"])
        message = error["msg"]
        error_type = error["type"]

        print(f"[{idx}] Field : {field}")
        print(f"    Type  : {error_type}")
        print(f"    Error : {message}")
        print()

    print("=" * 80)
