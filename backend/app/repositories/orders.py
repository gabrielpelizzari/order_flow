from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from app.core.database import get_connection
from app.schemas.events import utc_now_iso
from app.schemas.orders import OrderCreatePayload


def row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row)


def create_order_record(
    payload: OrderCreatePayload,
    order_event: dict[str, Any],
) -> dict[str, Any]:
    order_id = order_event["data"]["order_id"]
    now = order_event["occurred_at"]
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO orders (
                id, customer_name, customer_email, status, total_cents, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                payload.customer.name,
                payload.customer.email,
                "PENDING",
                payload.total_cents,
                now,
                now,
            ),
        )
        for item in payload.items:
            line_total_cents = item.quantity * item.unit_price_cents
            connection.execute(
                """
                INSERT INTO order_items (
                    id, order_id, sku, name, quantity, unit_price_cents, line_total_cents
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    order_id,
                    item.sku,
                    item.name,
                    item.quantity,
                    item.unit_price_cents,
                    line_total_cents,
                ),
            )
        add_order_event_with_connection(connection, order_id, order_event)
        order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return row_to_dict(order)


def add_order_event(order_id: str, event: dict[str, Any]) -> None:
    with get_connection() as connection:
        add_order_event_with_connection(connection, order_id, event)


def add_order_event_with_connection(connection: Any, order_id: str, event: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO order_events (id, order_id, event_type, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event["event_id"],
            order_id,
            event["event_type"],
            json.dumps(event, separators=(",", ":")),
            event["occurred_at"],
        ),
    )


def list_orders(status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    query = "SELECT * FROM orders"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [row_to_dict(row) for row in rows]


def get_order(order_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_order_detail(order_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return None
        items = connection.execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid ASC",
            (order_id,),
        ).fetchall()
        events = connection.execute(
            "SELECT * FROM order_events WHERE order_id = ? ORDER BY created_at ASC",
            (order_id,),
        ).fetchall()
        notifications = connection.execute(
            "SELECT * FROM notifications WHERE order_id = ? ORDER BY created_at ASC",
            (order_id,),
        ).fetchall()
    detail = row_to_dict(order)
    detail["items"] = [row_to_dict(row) for row in items]
    detail["events"] = [row_to_dict(row) for row in events]
    detail["notifications"] = [row_to_dict(row) for row in notifications]
    return detail


def list_order_events(order_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM order_events WHERE order_id = ? ORDER BY created_at ASC",
            (order_id,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def update_order_status(order_id: str, status: str) -> dict[str, Any] | None:
    now = utc_now_iso()
    with get_connection() as connection:
        connection.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, order_id),
        )
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return row_to_dict(row) if row else None


def add_notification(order_id: str, event_type: str, message: str, channel: str = "console") -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO notifications (id, order_id, event_type, message, channel, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(uuid4()), order_id, event_type, message, channel, utc_now_iso()),
        )


def is_event_processed(event_id: str, consumer_name: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ? AND consumer_name = ?",
            (event_id, consumer_name),
        ).fetchone()
    return row is not None


def mark_event_processed(event_id: str, consumer_name: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO processed_events (event_id, consumer_name, processed_at)
            VALUES (?, ?, ?)
            """,
            (event_id, consumer_name, utc_now_iso()),
        )
