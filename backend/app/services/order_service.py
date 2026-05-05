from __future__ import annotations

from typing import Callable
from uuid import uuid4

from app.repositories.orders import (
    create_order_record,
    get_order_detail,
    list_order_events,
    list_orders,
)
from app.schemas.events import build_event
from app.schemas.orders import OrderCreatePayload
from app.services.event_publisher import publish_domain_event


ALLOWED_TRANSITIONS = {
    "PENDING": {"PAYMENT_APPROVED", "PAYMENT_REJECTED"},
    "PAYMENT_APPROVED": {"STOCK_RESERVED", "STOCK_FAILED"},
    "STOCK_RESERVED": {"READY_TO_SHIP"},
    "PAYMENT_REJECTED": set(),
    "STOCK_FAILED": set(),
    "READY_TO_SHIP": set(),
}


def validate_order_total(payload: OrderCreatePayload) -> int:
    expected_total = sum(item.quantity * item.unit_price_cents for item in payload.items)
    if expected_total != payload.total_cents:
        raise ValueError(
            f"Order total_cents does not match item sum: expected {expected_total}, got {payload.total_cents}"
        )
    return expected_total


def apply_status_transition(current_status: str, target_status: str) -> str:
    allowed_targets = ALLOWED_TRANSITIONS.get(current_status)
    if allowed_targets is None or target_status not in allowed_targets:
        raise ValueError(f"Invalid status transition from {current_status} to {target_status}")
    return target_status


def create_order(
    payload: OrderCreatePayload,
    publisher: Callable[[str, dict], None] = publish_domain_event,
) -> dict:
    validate_order_total(payload)
    order_id = str(uuid4())
    correlation_id = str(uuid4())
    event = build_event(
        event_type="order.created",
        producer="api",
        correlation_id=correlation_id,
        data={
            "order_id": order_id,
            "customer_name": payload.customer.name,
            "customer_email": payload.customer.email,
            "items": [item.model_dump() for item in payload.items],
            "total_cents": payload.total_cents,
            "simulation": payload.simulation,
        },
    )
    order = create_order_record(payload, event)
    publisher("order.created", event)
    return order


def get_orders(status: str | None, limit: int, offset: int) -> list[dict]:
    return list_orders(status=status, limit=limit, offset=offset)


def get_order_by_id(order_id: str) -> dict | None:
    return get_order_detail(order_id)


def get_events_for_order(order_id: str) -> list[dict]:
    return list_order_events(order_id)
