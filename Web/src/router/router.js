

import { createRouter, createWebHistory } from 'vue-router';
import login from '../components/login.vue'


const routes = [
  { path: '/login', name: 'login', component: login, meta: { requiresAuth: false } },
]
const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;