from pydantic import ValidationError


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
