<template>
  <section class="page" v-if="ordersStore.currentOrder">
    <div class="page-header">
      <div>
        <h1>Order {{ shortId(ordersStore.currentOrder.id) }}</h1>
        <p>{{ ordersStore.currentOrder.customer_name }}</p>
      </div>
      <StatusBadge :status="ordersStore.currentOrder.status" />
    </div>

    <div class="detail-grid">
      <section class="panel">
        <h2>Items</h2>
        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Qty</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in ordersStore.currentOrder.items" :key="item.id">
              <td>{{ item.sku }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ formatMoney(item.line_total_cents) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>Timeline</h2>
        <OrderTimeline :events="ordersStore.currentEvents" />
      </section>
    </div>

    <section class="panel">
      <h2>Notifications</h2>
      <ul class="notifications">
        <li v-for="notification in ordersStore.currentOrder.notifications" :key="notification.id">
          <span>{{ notification.message }}</span>
          <time>{{ formatDate(notification.created_at) }}</time>
        </li>
        <li v-if="!ordersStore.currentOrder.notifications.length" class="empty">No notifications yet.</li>
      </ul>
    </section>
  </section>
  <p v-else-if="ordersStore.error" class="error">{{ ordersStore.error }}</p>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import OrderTimeline from '../components/OrderTimeline.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useOrdersStore } from '../stores/orders'

const props = defineProps<{ id: string }>()
const ordersStore = useOrdersStore()
const finalStatuses = new Set(['PAYMENT_REJECTED', 'STOCK_FAILED', 'READY_TO_SHIP'])
let pollingHandle: number | undefined

const shouldPoll = computed(() => {
  const status = ordersStore.currentOrder?.status
  return status ? !finalStatuses.has(status) : true
})

onMounted(async () => {
  await ordersStore.fetchOrder(props.id)
  pollingHandle = window.setInterval(async () => {
    if (shouldPoll.value) {
      await ordersStore.fetchOrder(props.id)
    }
  }, 3000)
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
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value))
}
</script>
