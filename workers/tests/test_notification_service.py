from worker_app.services.notification_service import build_notification_message


def test_build_notification_message_uses_event_type_and_order_id():
    message = build_notification_message(
        {
            "event_type": "order.ready_to_ship",
            "data": {"order_id": "order-123"},
        }
    )

    assert "order-123" in message
    assert "ready to ship" in message.lower()


def test_build_notification_message_includes_payment_rejection_simulation_reason():
    message = build_notification_message(
        {
            "event_type": "payment.rejected",
            "data": {
                "order_id": "order-123",
                "simulation": "PAYMENT_CARD_NO_LIMIT",
            },
        }
    )

    assert "order-123" in message
    assert "card without limit" in message.lower()
