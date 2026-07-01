from api_integration.mail.compose import _compose_reply_text


def test_case_1_both_error_and_rfq_id():
    """PARTIAL_SUCCESS_REPLY_TEMPLATE when both error and rfq_id present."""
    meta = {"subject": "Test RFQ Request", "date": "2026-06-28"}
    body = "Original email body content here."
    result = _compose_reply_text(
        meta=meta,
        body=body,
        rfq_info={"error": "PUT request failed", "rfq_id": 12345},
    )
    assert "Мы автоматически создали RFQ:" in result
    assert "Предупреждение:" in result
    assert "PUT request failed" in result
    assert "Extra info" not in result  # default extra_on_success is ""


def test_case_2_error_only():
    """ERROR_REPLY_TEMPLATE when only error present."""
    meta = {"subject": "Test RFQ Request", "date": "2026-06-28"}
    body = "Original email body content here."
    result = _compose_reply_text(
        meta=meta,
        body=body,
        rfq_info={"error": "No RFQ template found", "rfq_id": None},
    )
    assert "Нам не удалось автоматически создать RFQ." in result
    assert "No RFQ template found" in result


def test_case_3_rfq_id_only():
    """SUCCESS_REPLY_TEMPLATE when only rfq_id present."""
    meta = {"subject": "Test RFQ Request", "date": "2026-06-28"}
    body = "Original email body content here."
    result = _compose_reply_text(
        meta=meta,
        body=body,
        rfq_info={"error": None, "rfq_id": 12345},
    )
    assert "Мы автоматически создали RFQ:" in result
    assert "https://lk.7rights.ru/admin/newRfq/12345" in result
    assert "Extra info" not in result  # default extra_on_success is ""


def test_case_4_neither_none():
    """ERROR_REPLY_TEMPLATE with generic message when rfq_info is None."""
    meta = {"subject": "Test RFQ Request", "date": "2026-06-28"}
    body = "Original email body content here."
    result = _compose_reply_text(
        meta=meta,
        body=body,
        rfq_info=None,
    )
    assert "Нам не удалось автоматически создать RFQ." in result
    assert "(unable to generate rfq link or error message)" in result
    assert "Extra info" not in result  # default extra_on_success is ""


def test_case_5_extra_on_success_from_rfq_excel():
    """extra_on_success is inserted when provided."""
    meta = {"subject": "Test RFQ Request", "date": "2026-06-28"}
    body = "Original email body content here."
    result = _compose_reply_text(
        meta=meta,
        body=body,
        rfq_info={"error": None, "rfq_id": 12345},
        extra_on_success="Требования из Excel",
    )
    assert "Требования из Excel" in result
    assert "Мы автоматически создали RFQ:" in result
