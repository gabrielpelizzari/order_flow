<template>
  <span class="status-badge" :class="statusClass">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { OrderStatus } from '../api/orders'

const props = defineProps<{ status: OrderStatus | string }>()

const label = computed(() => props.status.replace(/_/g, ' '))
const statusClass = computed(() => `status-${props.status.toLowerCase()}`)
</script>
