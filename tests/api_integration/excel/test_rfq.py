import pytest

from api_integration.excel.rfq import (
    _copy_price_rating_values,
    _parse_percent_range_last,
)


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


class TestCopyPriceRatingValues:
    def test_price_values_only(self):
        result = {
            "price_green_finish_percent": 5.0,
            "price_yellow_finish_percent": 10.0,
        }
        _copy_price_rating_values(result)
        assert result["price_green_finish_percent"] == 5.0
        assert result["price_yellow_finish_percent"] == 10.0
        assert result["rating_green_finish_value"] == 5.0
        assert result["rating_yellow_finish_value"] == 10.0

    def test_rating_values_only(self):
        result = {"rating_green_finish_value": 15.0, "rating_yellow_finish_value": 25.0}
        _copy_price_rating_values(result)
        assert result["rating_green_finish_value"] == 15.0
        assert result["rating_yellow_finish_value"] == 25.0
        assert result["price_green_finish_percent"] == 15.0
        assert result["price_yellow_finish_percent"] == 25.0

    def test_both_pairs_present(self):
        result = {
            "price_green_finish_percent": 5.0,
            "price_yellow_finish_percent": 10.0,
            "rating_green_finish_value": 15.0,
            "rating_yellow_finish_value": 25.0,
        }
        _copy_price_rating_values(result)
        assert result["price_green_finish_percent"] == 5.0
        assert result["price_yellow_finish_percent"] == 10.0
        assert result["rating_green_finish_value"] == 15.0
        assert result["rating_yellow_finish_value"] == 25.0

    def test_neither_pair_present(self):
        result = {"other_field": "value"}
        _copy_price_rating_values(result)
        assert "price_green_finish_percent" not in result
        assert "price_yellow_finish_percent" not in result
        assert "rating_green_finish_value" not in result
        assert "rating_yellow_finish_value" not in result

    def test_partial_price_values(self):
        result = {"price_green_finish_percent": 5.0}
        _copy_price_rating_values(result)
        assert result["price_green_finish_percent"] == 5.0
        assert result["price_yellow_finish_percent"] == 0.0
        assert result["rating_green_finish_value"] == 5.0
        assert result["rating_yellow_finish_value"] == 0.0

    def test_partial_rating_values(self):
        result = {"rating_yellow_finish_value": 25.0}
        _copy_price_rating_values(result)
        assert result["rating_yellow_finish_value"] == 25.0
        assert result["rating_green_finish_value"] == 0.0
        assert result["price_yellow_finish_percent"] == 25.0
        assert result["price_green_finish_percent"] == 0.0

    def test_existing_rating_not_overwritten(self):
        result = {
            "price_green_finish_percent": 5.0,
            "rating_green_finish_value": 50.0,
        }
        _copy_price_rating_values(result)
        assert result["rating_green_finish_value"] == 50.0

    def test_existing_price_not_overwritten(self):
        result = {
            "rating_green_finish_value": 15.0,
            "price_green_finish_percent": 5.0,
        }
        _copy_price_rating_values(result)
        assert result["price_green_finish_percent"] == 5.0
