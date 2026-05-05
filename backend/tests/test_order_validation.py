import pytest

from app.schemas.orders import CustomerPayload, OrderCreatePayload, OrderItemPayload
from app.services.order_service import validate_order_total


def test_validate_order_total_accepts_matching_sum():
    payload = OrderCreatePayload(
        customer=CustomerPayload(name="Ana", email="ana@example.com"),
        items=[
            OrderItemPayload(
                sku="SKU-001",
                name="Keyboard",
                quantity=2,
                unit_price_cents=1500,
            ),
            OrderItemPayload(
                sku="SKU-002",
                name="Mouse",
                quantity=1,
                unit_price_cents=2000,
            ),
        ],
        total_cents=5000,
    )

    assert validate_order_total(payload) == 5000


def test_validate_order_total_rejects_mismatched_sum():
    payload = OrderCreatePayload(
        customer=CustomerPayload(name="Ana"),
        items=[
            OrderItemPayload(
                sku="SKU-001",
                name="Keyboard",
                quantity=2,
                unit_price_cents=1500,
            )
        ],
        total_cents=9999,
    )

    with pytest.raises(ValueError, match="does not match"):
        validate_order_total(payload)
