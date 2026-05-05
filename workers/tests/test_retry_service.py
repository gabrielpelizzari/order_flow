import json

import pytest

from worker_app.services import retry_service


class FakeMethod:
    delivery_tag = "tag-1"


class FakeChannel:
    def __init__(self):
        self.acks = []

    def basic_ack(self, delivery_tag):
        self.acks.append(delivery_tag)


def test_callback_sends_missing_required_data_field_to_dlq_without_retry(monkeypatch):
    dlq_events = []
    retry_events = []
    channel = FakeChannel()
    event = {
        "event_id": "event-1",
        "event_type": "order.created",
        "correlation_id": "correlation-1",
        "data": {"total_cents": 19900},
        "metadata": {"retry_count": 0},
    }

    monkeypatch.setattr(retry_service, "publish_to_dlq", lambda channel, event: dlq_events.append(event))
    monkeypatch.setattr(
        retry_service,
        "publish_to_queue",
        lambda channel, queue_name, event: retry_events.append((queue_name, event)),
    )

    callback = retry_service.make_callback(
        queue_name="q.payment.order_created",
        consumer_name="payment-worker",
        expected_event_types={"order.created"},
        required_data_fields={"order_id", "total_cents"},
        processor=lambda event, channel: pytest.fail("processor should not receive invalid payload"),
    )

    callback(channel, FakeMethod(), None, json.dumps(event).encode("utf-8"))

    assert len(dlq_events) == 1
    assert dlq_events[0]["event_type"] == "invalid.payload"
    assert "Missing required data field: order_id" in dlq_events[0]["data"]["reason"]
    assert retry_events == []
    assert channel.acks == ["tag-1"]
