from app.schemas.events import build_event


def test_build_event_includes_required_contract_fields():
    event = build_event(
        event_type="order.created",
        producer="api",
        correlation_id="correlation-123",
        data={"order_id": "order-123", "total_cents": 19900},
    )

    assert event["event_id"]
    assert event["event_type"] == "order.created"
    assert event["schema_version"] == 1
    assert event["occurred_at"]
    assert event["correlation_id"] == "correlation-123"
    assert event["producer"] == "api"
    assert event["data"]["order_id"] == "order-123"
    assert event["metadata"]["retry_count"] == 0
