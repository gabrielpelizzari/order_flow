import { http } from './http'

export type OrderStatus =
  | 'PENDING'
  | 'PAYMENT_APPROVED'
  | 'PAYMENT_REJECTED'
  | 'STOCK_RESERVED'
  | 'STOCK_FAILED'
  | 'READY_TO_SHIP'

export type OrderItemPayload = {
  sku: string
  name: string
  quantity: number
  unit_price_cents: number
}

export type OrderSimulation =
  | 'NONE'
  | 'PAYMENT_CARD_NO_LIMIT'
  | 'PAYMENT_INVALID_CARD'
  | 'PAYMENT_GATEWAY_ERROR'
  | 'STOCK_UNAVAILABLE'

export type OrderCreatePayload = {
  customer: {
    name: string
    email?: string | null
  }
  items: OrderItemPayload[]
  total_cents: number
  simulation?: OrderSimulation
}

export type OrderListItem = {
  id: string
  customer_name: string
  customer_email: string | null
  status: OrderStatus
  total_cents: number
  created_at: string
  updated_at: string
}

export type OrderItem = {
  id: string
  order_id: string
  sku: string
  name: string
  quantity: number
  unit_price_cents: number
  line_total_cents: number
}

export type OrderEvent = {
  id: string
  order_id: string
  event_type: string
  payload_json: string
  created_at: string
}

export type Notification = {
  id: string
  order_id: string
  event_type: string
  message: string
  channel: string
  created_at: string
}

export type OrderDetail = OrderListItem & {
  items: OrderItem[]
  events: OrderEvent[]
  notifications: Notification[]
}

export async function fetchOrders(status?: string) {
  const response = await http.get<OrderListItem[]>('/orders', {
    params: status ? { status } : undefined,
  })
  return response.data
}

export async function fetchOrder(id: string) {
  const response = await http.get<OrderDetail>(`/orders/${id}`)
  return response.data
}

export async function fetchOrderEvents(id: string) {
  const response = await http.get<OrderEvent[]>(`/orders/${id}/events`)
  return response.data
}

export async function createOrder(payload: OrderCreatePayload) {
  const response = await http.post<OrderListItem>('/orders', payload)
  return response.data
}
