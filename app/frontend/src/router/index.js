import { createRouter, createWebHistory } from 'vue-router'
import { authGuard } from './authGuard'
import { authService } from '@/services/authService'

const routes = [
  {
    path: '/',
    redirect: () => {
      // Check if user has a token - let server validate expiration
      const isAuthenticated = authService.isAuthenticated()
      // If authenticated, go to csv, otherwise login
      return isAuthenticated ? '/csv' : '/login'
    }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import(/* webpackChunkName: "login" */ '../components/Login.vue'),
    beforeEnter: authGuard.alreadyAuthenticated
  },
  {
    path: '/csv',
    name: 'csv',
    component: () => import(/* webpackChunkName: "csv" */ '../views/CSVView.vue'),
    beforeEnter: authGuard.requiresAuth
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
