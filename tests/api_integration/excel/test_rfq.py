import pytest

from api_integration.excel.rfq import _parse_percent_range_last


@pytest.mark.parametrize(
    "value,expected",
    [
        ("92.99% - 85%", 85.0),
        ("92.99%-85%", 85.0),
        ("92%-85.00%", 85.0),
        ("92.99 - 85", 85.0),
        ("92.99-85", 85.0),
        ("92-85.00", 85.0),
    ],
)
def test_parse_percent_range_last_specified_formats(
    value: str, expected: float
) -> None:
    assert _parse_percent_range_last(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("85%", 85.0),
        ("85", 85.0),
        ("85,5%", 85.5),
        (" 92 - 85.00 ", 85.0),
        ("92-0", 0.0),
        ("92-0,00", 0.0),
        ("92.5-85,75", 85.75),
        ("92,5-85.75", 85.75),
    ],
)
def test_parse_percent_range_last_extra(value: str, expected: float) -> None:
    assert _parse_percent_range_last(value) == expected
