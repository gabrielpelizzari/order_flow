<template>
  <form class="panel form-stack" @submit.prevent="submit">
    <label>
      Customer name
      <input v-model="customerName" required autocomplete="name" />
    </label>
    <label>
      Customer email
      <input v-model="customerEmail" type="email" autocomplete="email" />
    </label>
    <label>
      Simulate event
      <select v-model="simulation">
        <option value="NONE">No simulation</option>
        <option value="PAYMENT_CARD_NO_LIMIT">Card without limit</option>
        <option value="PAYMENT_INVALID_CARD">Invalid card data</option>
        <option value="PAYMENT_GATEWAY_ERROR">Payment gateway error</option>
        <option value="STOCK_UNAVAILABLE">Stock unavailable</option>
      </select>
    </label>

    <section class="items-editor">
      <div class="section-row">
        <h2>Items</h2>
        <button class="secondary" type="button" @click="addItem">Add item</button>
      </div>

      <div v-for="(item, index) in items" :key="index" class="item-row">
        <label class="product-field">
          Product
          <select v-model="item.sku" required @change="syncProduct(item)">
            <option v-for="product in products" :key="product.sku" :value="product.sku">
              {{ product.name }}
            </option>
          </select>
        </label>
        <label>
          Qty
          <input v-model.number="item.quantity" min="1" required type="number" />
        </label>
        <label>
          Unit cents
          <input :value="item.unit_price_cents" readonly type="number" />
        </label>
        <button class="icon-button" type="button" title="Remove item" @click="removeItem(index)">x</button>
      </div>
    </section>

    <div class="summary-row">
      <span>Total</span>
      <strong>{{ formatMoney(totalCents) }}</strong>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <button class="primary" type="submit" :disabled="submitting">
      {{ submitting ? 'Creating...' : 'Create order' }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { OrderCreatePayload, OrderItemPayload, OrderSimulation } from '../api/orders'

const emit = defineEmits<{ submit: [payload: OrderCreatePayload] }>()
defineProps<{ submitting?: boolean; error?: string | null }>()

const products = [
  { sku: 'SKU-MOUSE', name: 'Mouse', unit_price_cents: 5900 },
  { sku: 'SKU-KEYBOARD', name: 'Keyboard', unit_price_cents: 19900 },
  { sku: 'SKU-MONITOR', name: 'Monitor', unit_price_cents: 89900 },
  { sku: 'SKU-HEADSET', name: 'Headset', unit_price_cents: 12900 },
  { sku: 'SKU-WEBCAM', name: 'Webcam', unit_price_cents: 15900 },
]

const customerName = ref('')
const customerEmail = ref('')
const simulation = ref<OrderSimulation>('NONE')
const items = reactive<OrderItemPayload[]>([createItem('SKU-KEYBOARD')])

const totalCents = computed(() =>
  items.reduce((total, item) => total + item.quantity * item.unit_price_cents, 0),
)

function addItem() {
  items.push(createItem('SKU-MOUSE'))
}

function removeItem(index: number) {
  if (items.length > 1) {
    items.splice(index, 1)
  }
}

function createItem(sku: string): OrderItemPayload {
  const product = findProduct(sku)
  return {
    sku: product.sku,
    name: product.name,
    quantity: 1,
    unit_price_cents: product.unit_price_cents,
  }
}

function syncProduct(item: OrderItemPayload) {
  const product = findProduct(item.sku)
  item.name = product.name
  item.unit_price_cents = product.unit_price_cents
}

function findProduct(sku: string) {
  return products.find((product) => product.sku === sku) ?? products[0]
}

async function submit() {
  emit('submit', {
    customer: {
      name: customerName.value,
      email: customerEmail.value || null,
    },
    items: items.map((item) => ({ ...item })),
    total_cents: totalCents.value,
    simulation: simulation.value,
  })
}

function formatMoney(cents: number) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(cents / 100)
}
</script>
