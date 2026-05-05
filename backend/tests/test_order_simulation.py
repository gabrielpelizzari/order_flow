from app.schemas.orders import CustomerPayload, OrderCreatePayload, OrderItemPayload
from app.core.database import init_db
from app.services import order_service


def test_create_order_defaults_missing_simulation_to_none(monkeypatch, tmp_path):
    published = []
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "orderflow.db"))
    init_db()

    payload = OrderCreatePayload(
        customer=CustomerPayload(name="Ana"),
        items=[
            OrderItemPayload(
                sku="SKU-001",
                name="Keyboard",
                quantity=1,
                unit_price_cents=19900,
            )
        ],
        total_cents=19900,
    )

    order_service.create_order(payload, publisher=lambda routing_key, event: published.append(event))

    assert published[0]["data"]["simulation"] == "NONE"


def test_create_order_includes_requested_simulation_in_event(monkeypatch, tmp_path):
    published = []
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "orderflow.db"))
    init_db()

    payload = OrderCreatePayload(
        customer=CustomerPayload(name="Ana"),
        items=[
            OrderItemPayload(
                sku="SKU-001",
                name="Keyboard",
                quantity=1,
                unit_price_cents=19900,
            )
        ],
        total_cents=19900,
        simulation="PAYMENT_CARD_NO_LIMIT",
    )

    order_service.create_order(payload, publisher=lambda routing_key, event: published.append(event))

    assert published[0]["data"]["simulation"] == "PAYMENT_CARD_NO_LIMIT"
