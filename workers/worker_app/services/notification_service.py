from __future__ import annotations

from typing import Any

from app.repositories.orders import add_notification, is_event_processed, mark_event_processed


CONSUMER_NAME = "notification-worker"

NOTIFICATION_TEXT = {
    "payment.approved": "Payment approved for order {order_id}.",
    "payment.rejected": "Payment rejected for order {order_id}.",
    "stock.failed": "Stock reservation failed for order {order_id}.",
    "order.ready_to_ship": "Order {order_id} is ready to ship.",
}

SIMULATION_REASON_TEXT = {
    "PAYMENT_CARD_NO_LIMIT": "card without limit",
    "PAYMENT_INVALID_CARD": "invalid card data",
    "PAYMENT_GATEWAY_ERROR": "payment gateway returned an error",
    "STOCK_UNAVAILABLE": "stock unavailable",
}


def build_notification_message(event: dict[str, Any]) -> str:
    order_id = event["data"]["order_id"]
    template = NOTIFICATION_TEXT.get(event["event_type"], "Event {event_type} for order {order_id}.")
    message = template.format(order_id=order_id, event_type=event["event_type"])
    simulation = event["data"].get("simulation")
    reason = SIMULATION_REASON_TEXT.get(simulation)
    if reason and event["event_type"] in {"payment.rejected", "stock.failed"}:
        return f"{message} Reason: {reason}."
    return message


def process_notification_event(event: dict[str, Any], channel: Any) -> None:
    if is_event_processed(event["event_id"], CONSUMER_NAME):
        return
    order_id = event["data"]["order_id"]
    message = build_notification_message(event)
    add_notification(order_id, event["event_type"], message)
    print(f"[{event['correlation_id']}] {message}")
    mark_event_processed(event["event_id"], CONSUMER_NAME)
