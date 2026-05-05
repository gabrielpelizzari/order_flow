from app.core.rabbitmq import setup_topology


class FakeChannel:
    def __init__(self):
        self.bindings = []
        self.queues = []

    def exchange_declare(self, **kwargs):
        pass

    def queue_declare(self, **kwargs):
        self.queues.append(kwargs)

    def queue_bind(self, **kwargs):
        self.bindings.append(kwargs)


def test_notification_retry_routing_key_is_isolated_from_stock_queue():
    channel = FakeChannel()

    setup_topology(channel)

    notification_bindings = [
        binding["routing_key"]
        for binding in channel.bindings
        if binding["queue"] == "q.notification.events"
    ]
    stock_bindings = [
        binding["routing_key"]
        for binding in channel.bindings
        if binding["queue"] == "q.stock.payment_approved"
    ]

    assert "notification.retry" in notification_bindings
    assert "notification.retry" not in stock_bindings
