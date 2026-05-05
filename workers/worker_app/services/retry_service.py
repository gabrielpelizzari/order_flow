from __future__ import annotations

import json
from typing import Any, Callable
from uuid import uuid4

from app.core.config import get_settings
from app.core.rabbitmq import RETRY_QUEUES, publish_to_dlq, publish_to_queue
from app.schemas.events import utc_now_iso


def parse_event(body: bytes, required_data_fields: set[str] | None = None) -> dict[str, Any]:
    event = json.loads(body.decode("utf-8"))
    if not isinstance(event, dict):
        raise ValueError("Event body must be a JSON object")
    for field in ("event_id", "event_type", "correlation_id", "data", "metadata"):
        if field not in event:
            raise ValueError(f"Missing required event field: {field}")
    if not isinstance(event["data"], dict):
        raise ValueError("Event data must be an object")
    if not isinstance(event["metadata"], dict):
        raise ValueError("Event metadata must be an object")
    for field in required_data_fields or set():
        if field not in event["data"]:
            raise ValueError(f"Missing required data field: {field}")
    return event


def build_invalid_payload_event(raw_body: bytes, reason: str, consumer_name: str) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "event_type": "invalid.payload",
        "schema_version": 1,
        "occurred_at": utc_now_iso(),
        "correlation_id": str(uuid4()),
        "producer": consumer_name,
        "data": {"raw_body": raw_body.decode("utf-8", errors="replace"), "reason": reason},
        "metadata": {"retry_count": get_settings().max_retries},
    }


def retry_or_dlq(channel: Any, queue_name: str, event: dict[str, Any]) -> None:
    retry_count = int(event.get("metadata", {}).get("retry_count", 0))
    if retry_count >= get_settings().max_retries:
        publish_to_dlq(channel, event)
        return
    event.setdefault("metadata", {})["retry_count"] = retry_count + 1
    publish_to_queue(channel, RETRY_QUEUES[queue_name], event)


def make_callback(
    *,
    queue_name: str,
    consumer_name: str,
    expected_event_types: set[str],
    required_data_fields: set[str] | None = None,
    processor: Callable[[dict[str, Any], Any], None],
) -> Callable:
    def callback(channel: Any, method: Any, properties: Any, body: bytes) -> None:
        try:
            event = parse_event(body, required_data_fields=required_data_fields)
            if event["event_type"] not in expected_event_types:
                raise ValueError(f"Unexpected event_type for {consumer_name}: {event['event_type']}")
            processor(event, channel)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except ValueError as exc:
            invalid_event = build_invalid_payload_event(body, str(exc), consumer_name)
            publish_to_dlq(channel, invalid_event)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            retry_or_dlq(channel, queue_name, event)
            channel.basic_ack(delivery_tag=method.delivery_tag)

    return callback
