from __future__ import annotations

import json
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.core.config import get_settings


EVENT_EXCHANGE = "orderflow.events"
DLX_EXCHANGE = "orderflow.dlx"

MAIN_QUEUES = {
    "q.payment.order_created": ["order.created"],
    "q.stock.payment_approved": ["payment.approved"],
    "q.shipping.stock_reserved": ["stock.reserved"],
    "q.notification.events": [
        "payment.approved",
        "payment.rejected",
        "stock.failed",
        "order.ready_to_ship",
        "notification.retry",
    ],
}

RETRY_QUEUES = {
    "q.payment.order_created": "q.payment.order_created.retry",
    "q.stock.payment_approved": "q.stock.payment_approved.retry",
    "q.shipping.stock_reserved": "q.shipping.stock_reserved.retry",
    "q.notification.events": "q.notification.events.retry",
}

RETRY_ROUTING_KEYS = {
    "q.payment.order_created.retry": "order.created",
    "q.stock.payment_approved.retry": "payment.approved",
    "q.shipping.stock_reserved.retry": "stock.reserved",
    "q.notification.events.retry": "notification.retry",
}


@contextmanager
def rabbitmq_channel() -> Iterator[Any]:
    import pika

    settings = get_settings()
    parameters = pika.URLParameters(settings.rabbitmq_url)
    connection = None
    last_error: Exception | None = None
    for _ in range(settings.rabbitmq_connection_attempts):
        try:
            connection = pika.BlockingConnection(parameters)
            break
        except pika.exceptions.AMQPConnectionError as exc:
            last_error = exc
            time.sleep(settings.rabbitmq_connection_retry_seconds)
    if connection is None:
        raise last_error or RuntimeError("Could not connect to RabbitMQ")
    try:
        channel = connection.channel()
        yield channel
    finally:
        connection.close()


def setup_topology(channel: Any) -> None:
    settings = get_settings()
    channel.exchange_declare(exchange=EVENT_EXCHANGE, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=DLX_EXCHANGE, exchange_type="topic", durable=True)

    for queue_name, routing_keys in MAIN_QUEUES.items():
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={"x-dead-letter-exchange": DLX_EXCHANGE},
        )
        for routing_key in routing_keys:
            channel.queue_bind(exchange=EVENT_EXCHANGE, queue=queue_name, routing_key=routing_key)

    for main_queue, retry_queue in RETRY_QUEUES.items():
        retry_routing_key = RETRY_ROUTING_KEYS[retry_queue]
        channel.queue_declare(
            queue=retry_queue,
            durable=True,
            arguments={
                "x-message-ttl": settings.retry_ttl_ms,
                "x-dead-letter-exchange": EVENT_EXCHANGE,
                "x-dead-letter-routing-key": retry_routing_key,
            },
        )

    channel.queue_declare(queue="q.orderflow.dlq", durable=True)
    channel.queue_bind(exchange=DLX_EXCHANGE, queue="q.orderflow.dlq", routing_key="#")


def publish_event(channel: Any, routing_key: str, event: dict[str, Any]) -> None:
    import pika

    channel.basic_publish(
        exchange=EVENT_EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            correlation_id=event["correlation_id"],
            message_id=event["event_id"],
        ),
    )


def publish_to_queue(channel: Any, queue_name: str, event: dict[str, Any]) -> None:
    import pika

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            correlation_id=event.get("correlation_id"),
            message_id=event.get("event_id"),
        ),
    )


def publish_to_dlq(channel: Any, event: dict[str, Any]) -> None:
    import pika

    channel.basic_publish(
        exchange=DLX_EXCHANGE,
        routing_key="dead." + event.get("event_type", "unknown"),
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            correlation_id=event.get("correlation_id"),
            message_id=event.get("event_id"),
        ),
    )
