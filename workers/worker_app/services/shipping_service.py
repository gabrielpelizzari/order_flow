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


CONSUMER_NAME = "shipping-worker"


def process_shipping_event(event: dict[str, Any], channel: Any) -> None:
    if is_event_processed(event["event_id"], CONSUMER_NAME):
        return
    order_id = event["data"]["order_id"]
    order = get_order(order_id)
    if not order:
        raise ValueError(f"Order not found: {order_id}")

    target_status = "READY_TO_SHIP"
    if order["status"] != target_status:
        apply_status_transition(order["status"], target_status)
        update_order_status(order_id, target_status)

    next_event = build_event(
        event_type="order.ready_to_ship",
        producer=CONSUMER_NAME,
        correlation_id=event["correlation_id"],
        data={**event["data"], "status": target_status},
    )
    add_order_event(order_id, next_event)
    publish_event(channel, "order.ready_to_ship", next_event)
    mark_event_processed(event["event_id"], CONSUMER_NAME)
