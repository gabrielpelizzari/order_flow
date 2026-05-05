from worker_app.services.payment_service import decide_payment_status
from worker_app.services.stock_service import decide_stock_status


def test_decide_payment_status_approves_when_simulation_is_none():
    assert decide_payment_status(simulation="NONE") == "PAYMENT_APPROVED"


def test_decide_payment_status_rejects_payment_simulations():
    payment_simulations = [
        "PAYMENT_CARD_NO_LIMIT",
        "PAYMENT_INVALID_CARD",
        "PAYMENT_GATEWAY_ERROR",
    ]

    for simulation in payment_simulations:
        assert decide_payment_status(simulation=simulation) == "PAYMENT_REJECTED"


def test_decide_stock_status_fails_when_stock_is_unavailable():
    assert decide_stock_status(simulation="STOCK_UNAVAILABLE") == "STOCK_FAILED"


def test_decide_stock_status_reserves_for_other_simulations():
    assert decide_stock_status(simulation="NONE") == "STOCK_RESERVED"
    assert decide_stock_status(simulation="PAYMENT_CARD_NO_LIMIT") == "STOCK_RESERVED"
