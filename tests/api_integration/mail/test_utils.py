"""Tests for mail.utils
Usage: pytest -v tests/
"""

import json

from api_integration.mail.utils import get_rfq_draft_url, is_trusted_email


class TestGetRfqDraftUrl:
    """Tests for get_rfq_draft_url function."""

    def test_default_template(self):
        rfq_id = 123
        result = get_rfq_draft_url(rfq_id)
        assert result == "https://lk.7rights.ru/admin/newRfq/123"

    def test_custom_template(self):
        rfq_id = 456
        template = "https://example.com/rfq/{rfq_id}/edit"
        result = get_rfq_draft_url(rfq_id, template)
        assert result == "https://example.com/rfq/456/edit"


class TestIsTrustedEmail:
    """Tests for is_trusted_email function."""

    def test_found_exact_match(self, tmp_path):
        trusted_file = tmp_path / "trusted.json"
        trusted_file.write_text(json.dumps(["user@example.com"]))
        assert is_trusted_email("user@example.com", str(trusted_file)) is True

    def test_found_case_insensitive(self, tmp_path):
        trusted_file = tmp_path / "trusted.json"
        trusted_file.write_text(json.dumps(["user@example.com"]))
        assert is_trusted_email("USER@EXAMPLE.COM", str(trusted_file)) is True

    def test_found_timofeevaan_sibur(self, tmp_path):
        trusted_file = tmp_path / "trusted.json"
        trusted_file.write_text(json.dumps(["timofeevaan@sibur.ru"]))
        assert is_trusted_email("timofeevaan@sibur.ru", str(trusted_file)) is True
        assert is_trusted_email("Timofeevaan@Sibur.Ru", str(trusted_file)) is True

    def test_not_found(self, tmp_path):
        trusted_file = tmp_path / "trusted.json"
        trusted_file.write_text(json.dumps(["other@example.com"]))
        assert is_trusted_email("unknown@example.com", str(trusted_file)) is False

    def test_file_not_exists(self, tmp_path):
        assert is_trusted_email("any@example.com", str(tmp_path / "none.json")) is False
