import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import OrdersList from './views/OrdersList.vue'
import OrderCreate from './views/OrderCreate.vue'
import OrderDetail from './views/OrderDetail.vue'
import './styles.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/orders' },
    { path: '/orders', component: OrdersList },
    { path: '/orders/new', component: OrderCreate },
    { path: '/orders/:id', component: OrderDetail, props: true },
  ],
})

createApp(App).use(createPinia()).use(router).mount('#app')
