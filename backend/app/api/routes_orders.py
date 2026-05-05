from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.orders import OrderCreatePayload, OrderCreateResponse, OrderDetailResponse, OrderEventResponse, OrderListItem
from app.services.event_publisher import EventPublishError
from app.services.order_service import create_order, get_events_for_order, get_order_by_id, get_orders


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
def post_order(payload: OrderCreatePayload) -> dict:
    try:
        return create_order(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except EventPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order was stored, but RabbitMQ publish failed. Retry or inspect pending orders.",
        ) from exc


@router.get("", response_model=list[OrderListItem])
def list_orders_route(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    return get_orders(status=status_filter, limit=limit, offset=offset)


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order_route(order_id: str) -> dict:
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get("/{order_id}/events", response_model=list[OrderEventResponse])
def get_order_events_route(order_id: str) -> list[dict]:
    if not get_order_by_id(order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return get_events_for_order(order_id)
