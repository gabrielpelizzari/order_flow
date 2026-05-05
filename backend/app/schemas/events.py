from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_event(
    *,
    event_type: str,
    producer: str,
    correlation_id: str,
    data: dict[str, Any],
    retry_count: int = 0,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "schema_version": SCHEMA_VERSION,
        "occurred_at": utc_now_iso(),
        "correlation_id": correlation_id,
        "producer": producer,
        "data": data,
        "metadata": {"retry_count": retry_count},
    }
