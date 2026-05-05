from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SimulationType = Literal[
    "NONE",
    "PAYMENT_CARD_NO_LIMIT",
    "PAYMENT_INVALID_CARD",
    "PAYMENT_GATEWAY_ERROR",
    "STOCK_UNAVAILABLE",
]


class CustomerPayload(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None


class OrderItemPayload(BaseModel):
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(gt=0)


class OrderCreatePayload(BaseModel):
    customer: CustomerPayload
    items: list[OrderItemPayload] = Field(min_length=1)
    total_cents: int = Field(gt=0)
    simulation: SimulationType = "NONE"


class OrderCreateResponse(BaseModel):
    id: str
    status: str
    total_cents: int
    created_at: str


class OrderListItem(BaseModel):
    id: str
    customer_name: str
    customer_email: str | None
    status: str
    total_cents: int
    created_at: str
    updated_at: str


class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    sku: str
    name: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int


class OrderEventResponse(BaseModel):
    id: str
    order_id: str
    event_type: str
    payload_json: str
    created_at: str


class NotificationResponse(BaseModel):
    id: str
    order_id: str
    event_type: str
    message: str
    channel: str
    created_at: str


class OrderDetailResponse(OrderListItem):
    items: list[OrderItemResponse]
    events: list[OrderEventResponse]
    notifications: list[NotificationResponse]
