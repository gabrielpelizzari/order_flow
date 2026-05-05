from __future__ import annotations

from app.core.rabbitmq import publish_event, rabbitmq_channel, setup_topology


class EventPublishError(RuntimeError):
    pass


def publish_domain_event(routing_key: str, event: dict) -> None:
    try:
        with rabbitmq_channel() as channel:
            setup_topology(channel)
            publish_event(channel, routing_key, event)
    except Exception as exc:  # pragma: no cover - exercised in integration/manual flow
        raise EventPublishError(str(exc)) from exc
