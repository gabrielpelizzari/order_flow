<template>
  <section class="page narrow">
    <div class="page-header">
      <div>
        <h1>Create order</h1>
        <p>Submit an order into the RabbitMQ processing flow.</p>
      </div>
    </div>
    <OrderForm :error="error" :submitting="submitting" @submit="handleSubmit" />
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import OrderForm from '../components/OrderForm.vue'
import type { OrderCreatePayload } from '../api/orders'
import { useOrdersStore } from '../stores/orders'

const router = useRouter()
const ordersStore = useOrdersStore()
const submitting = ref(false)
const error = ref<string | null>(null)

async function handleSubmit(payload: OrderCreatePayload) {
  if (submitting.value) return
  submitting.value = true
  error.value = null
  try {
    const order = await ordersStore.createOrder(payload)
    await router.push(`/orders/${order.id}`)
  } catch {
    error.value = ordersStore.error ?? 'Could not create order'
  } finally {
    submitting.value = false
  }
}
</script>
