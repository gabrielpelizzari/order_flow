from __future__ import annotations

from typing import Any

from app.core.rabbitmq import publish_event
from app.repositories.orders import (
    add_order_event,
    get_order,
    is_event_processed,
    mark_event_processed,
    update_order_status,
)
from app.schemas.events import build_event
from app.services.order_service import apply_status_transition


CONSUMER_NAME = "payment-worker"
PAYMENT_REJECTION_SIMULATIONS = {
    "PAYMENT_CARD_NO_LIMIT",
    "PAYMENT_INVALID_CARD",
    "PAYMENT_GATEWAY_ERROR",
}


def decide_payment_status(simulation: str = "NONE") -> str:
    return "PAYMENT_REJECTED" if simulation in PAYMENT_REJECTION_SIMULATIONS else "PAYMENT_APPROVED"


def process_payment_event(event: dict[str, Any], channel: Any) -> None:
    if is_event_processed(event["event_id"], CONSUMER_NAME):
        return
    order_id = event["data"]["order_id"]
    order = get_order(order_id)
    if not order:
        raise ValueError(f"Order not found: {order_id}")

    target_status = decide_payment_status(simulation=event["data"].get("simulation", "NONE"))
    if order["status"] != target_status:
        apply_status_transition(order["status"], target_status)
        update_order_status(order_id, target_status)

    event_type = "payment.approved" if target_status == "PAYMENT_APPROVED" else "payment.rejected"
    next_event = build_event(
        event_type=event_type,
        producer=CONSUMER_NAME,
        correlation_id=event["correlation_id"],
        data={**event["data"], "status": target_status},
    )
    add_order_event(order_id, next_event)
    publish_event(channel, event_type, next_event)
    mark_event_processed(event["event_id"], CONSUMER_NAME)
