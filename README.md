# OrderFlow

OrderFlow is a full-stack event-driven order processing system built with FastAPI, Vue.js, RabbitMQ, and SQLite.

It demonstrates how a mini store can create orders quickly through an API or frontend, then process payment, stock, shipping, and notifications asynchronously through RabbitMQ workers.

```text
Vue Frontend -> FastAPI API -> RabbitMQ -> Workers -> SQLite -> Vue Polling
```

## Overview

The user creates an order in the frontend. The API saves it as `PENDING`, publishes an `order.created` event, and the workers process the rest of the flow in the background.

The frontend keeps polling the API to show the current order status, event timeline, and notifications.

## Tech Stack

- Backend: Python, FastAPI, uv
- Frontend: Vue.js, Axios, Pinia
- Messaging: RabbitMQ
- Database: SQLite
- Local infrastructure: Docker and Docker Compose

## Architecture

```text
User
  -> Vue Frontend
  -> FastAPI API
  -> SQLite stores order as PENDING
  -> RabbitMQ receives order.created
  -> Workers process payment, stock, shipping, notifications
  -> SQLite stores status, events, and notifications
  -> Vue updates the screen via polling
```

Main order path:

```text
PENDING -> PAYMENT_APPROVED -> STOCK_RESERVED -> READY_TO_SHIP
```

Failure paths:

```text
PENDING -> PAYMENT_REJECTED
PENDING -> PAYMENT_APPROVED -> STOCK_FAILED
```

## How to Run

Requirements:

- Docker Desktop
- Docker Compose

Run the project:

```powershell
docker compose up --build
```

Run in the background:

```powershell
docker compose up -d --build
```

Stop the project:

```powershell
docker compose down
```

Reset the SQLite volume:

```powershell
docker compose down -v
```

## Project URLs

```text
Frontend:       http://localhost:5173
Create order:   http://localhost:5173/orders/new
API docs:       http://localhost:8000/docs
RabbitMQ UI:    http://localhost:15672
RabbitMQ login: guest / guest
```

## How to Test the Flow

### Frontend

1. Open `http://localhost:5173/orders/new`.
2. Enter a customer name.
3. Choose a product and quantity.
4. Choose a simulation scenario.
5. Click `Create order`.
6. Watch the order detail page update through polling.

### API

```powershell
$body = @{
  customer = @{
    name = "Ana"
    email = "ana@example.com"
  }
  items = @(
    @{
      sku = "SKU-KEYBOARD"
      name = "Keyboard"
      quantity = 1
      unit_price_cents = 19900
    }
  )
  total_cents = 19900
  simulation = "NONE"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/orders `
  -ContentType "application/json" `
  -Body $body
```

Useful API calls:

```powershell
Invoke-RestMethod http://localhost:8000/orders
Invoke-RestMethod http://localhost:8000/orders/ORDER_ID
Invoke-RestMethod http://localhost:8000/orders/ORDER_ID/events
```

## Simulation Scenarios

| Frontend option | API value | Result |
| --- | --- | --- |
| No simulation | `NONE` | `READY_TO_SHIP` |
| Card without limit | `PAYMENT_CARD_NO_LIMIT` | `PAYMENT_REJECTED` |
| Invalid card data | `PAYMENT_INVALID_CARD` | `PAYMENT_REJECTED` |
| Payment gateway error | `PAYMENT_GATEWAY_ERROR` | `PAYMENT_REJECTED` |
| Stock unavailable | `STOCK_UNAVAILABLE` | `STOCK_FAILED` |

## RabbitMQ Flow

Main exchange:

```text
orderflow.events
type: topic
```

Dead-letter exchange:

```text
orderflow.dlx
type: topic
```

Main routing keys:

```text
order.created
payment.approved
payment.rejected
stock.reserved
stock.failed
order.ready_to_ship
```

Main queues:

| Queue | Consumed by | Routing key |
| --- | --- | --- |
| `q.payment.order_created` | payment worker | `order.created` |
| `q.stock.payment_approved` | stock worker | `payment.approved` |
| `q.shipping.stock_reserved` | shipping worker | `stock.reserved` |
| `q.notification.events` | notification worker | payment, stock, and ready events |
| `q.orderflow.dlq` | dead-letter queue | failed messages |

Workers acknowledge messages only after processing. Transient failures go to retry queues, and messages that keep failing are sent to the DLQ.

