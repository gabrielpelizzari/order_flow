import { defineStore } from 'pinia'
import {
  createOrder,
  fetchOrder,
  fetchOrderEvents,
  fetchOrders,
  type OrderCreatePayload,
  type OrderDetail,
  type OrderEvent,
  type OrderListItem,
} from '../api/orders'

export const useOrdersStore = defineStore('orders', {
  state: () => ({
    orders: [] as OrderListItem[],
    currentOrder: null as OrderDetail | null,
    currentEvents: [] as OrderEvent[],
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchOrders(status?: string) {
      this.loading = true
      this.error = null
      try {
        this.orders = await fetchOrders(status || undefined)
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    async fetchOrder(id: string) {
      this.loading = true
      this.error = null
      try {
        this.currentOrder = await fetchOrder(id)
        this.currentEvents = this.currentOrder.events
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    async fetchOrderEvents(id: string) {
      this.currentEvents = await fetchOrderEvents(id)
    },
    async createOrder(payload: OrderCreatePayload) {
      this.error = null
      try {
        return await createOrder(payload)
      } catch (error) {
        this.error = getErrorMessage(error)
        throw error
      }
    },
  },
})

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response
    return response?.data?.detail ?? 'Request failed'
  }
  return error instanceof Error ? error.message : 'Unexpected error'
}
