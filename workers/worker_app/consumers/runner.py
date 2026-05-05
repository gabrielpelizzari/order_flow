from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.database import init_db
from app.core.rabbitmq import rabbitmq_channel, setup_topology
from worker_app.services.retry_service import make_callback


def run_consumer(
    *,
    queue_name: str,
    consumer_name: str,
    expected_event_types: set[str],
    required_data_fields: set[str] | None,
    processor: Callable[[dict, Any], None],
) -> None:
    init_db()
    with rabbitmq_channel() as channel:
        setup_topology(channel)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=make_callback(
                queue_name=queue_name,
                consumer_name=consumer_name,
                expected_event_types=expected_event_types,
                required_data_fields=required_data_fields,
                processor=processor,
            ),
        )
        print(f"{consumer_name} consuming {queue_name}")
        channel.start_consuming()
