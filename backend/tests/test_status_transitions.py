import pytest

from app.services.order_service import apply_status_transition


def test_apply_status_transition_allows_defined_flow():
    assert apply_status_transition("PENDING", "PAYMENT_APPROVED") == "PAYMENT_APPROVED"
    assert apply_status_transition("PAYMENT_APPROVED", "STOCK_RESERVED") == "STOCK_RESERVED"
    assert apply_status_transition("STOCK_RESERVED", "READY_TO_SHIP") == "READY_TO_SHIP"


def test_apply_status_transition_rejects_invalid_flow():
    with pytest.raises(ValueError, match="Invalid status transition"):
        apply_status_transition("PENDING", "READY_TO_SHIP")
