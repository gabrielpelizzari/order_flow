<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1>Orders</h1>
        <p>Current asynchronous order flow state.</p>
      </div>
      <RouterLink class="primary link-button" to="/orders/new">New order</RouterLink>
    </div>

    <div class="toolbar">
      <label>
        Status
        <select v-model="statusFilter" @change="ordersStore.fetchOrders(statusFilter)">
          <option value="">All</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
      <button class="secondary" type="button" @click="ordersStore.fetchOrders(statusFilter)">Refresh</button>
    </div>

    <p v-if="ordersStore.error" class="error">{{ ordersStore.error }}</p>

    <div class="panel table-panel">
      <table>
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer</th>
            <th>Status</th>
            <th>Total</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in ordersStore.orders" :key="order.id">
            <td><RouterLink :to="`/orders/${order.id}`">{{ shortId(order.id) }}</RouterLink></td>
            <td>{{ order.customer_name }}</td>
            <td><StatusBadge :status="order.status" /></td>
            <td>{{ formatMoney(order.total_cents) }}</td>
            <td>{{ formatDate(order.created_at) }}</td>
          </tr>
          <tr v-if="!ordersStore.orders.length">
            <td colspan="5" class="empty">No orders yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useOrdersStore } from '../stores/orders'

const ordersStore = useOrdersStore()
const statusFilter = ref('')
const statuses = ['PENDING', 'PAYMENT_APPROVED', 'PAYMENT_REJECTED', 'STOCK_RESERVED', 'STOCK_FAILED', 'READY_TO_SHIP']
let pollingHandle: number | undefined

onMounted(() => {
  ordersStore.fetchOrders()
  pollingHandle = window.setInterval(() => ordersStore.fetchOrders(statusFilter.value), 5000)
})

onUnmounted(() => {
  if (pollingHandle) window.clearInterval(pollingHandle)
})

function shortId(id: string) {
  return id.slice(0, 8)
}

function formatMoney(cents: number) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(cents / 100)
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}
</script>
