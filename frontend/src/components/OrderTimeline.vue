<template>
  <ol class="timeline">
    <li v-for="event in events" :key="event.id" class="timeline-item">
      <div class="timeline-dot"></div>
      <div>
        <strong>{{ event.event_type }}</strong>
        <time>{{ formatDate(event.created_at) }}</time>
      </div>
    </li>
  </ol>
</template>

<script setup lang="ts">
import type { OrderEvent } from '../api/orders'

defineProps<{ events: OrderEvent[] }>()

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(new Date(value))
}
</script>
