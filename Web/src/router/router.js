

import { createRouter, createWebHistory } from 'vue-router';
import login from '../components/login.vue'
import UW from '../user/UW.vue'
import AW from '../admin/AW.vue'
import ImageRecognition from '../user/ImageRecognition.vue'
import BatchProcessing from '../user/BatchProcessing.vue'
import RealtimeDetection from '../user/RealtimeDetection.vue'
import UserProfile from '../user/UserProfile.vue'
import UserManagement from '../admin/UserManagement.vue'
import LogViewer from '../admin/LogViewer.vue'
import DataAnalysis from '../admin/DataAnalysis.vue'

const routes = [
  { path: '/login', name: 'login', component: login, meta: { requiresAuth: false } },
  { 
    path: '/user', 
    name: 'user', 
    component: UW,
    meta: { requiresAuth: true, userType: 'user' },
    redirect: '/user/image-recognition',
    children: [
      { path: '/user/image-recognition', name: 'imageRecognition', component: ImageRecognition, meta: { requiresAuth: true, userType: 'user' } },
      { path: '/user/batch-processing', name: 'batchProcessing', component: BatchProcessing, meta: { requiresAuth: true, userType: 'user' } },
      { path: '/user/realtime-detection', name: 'realtimeDetection', component: RealtimeDetection, meta: { requiresAuth: true, userType: 'user' } },
      { path: '/user/profile', name: 'userProfile', component: UserProfile, meta: { requiresAuth: true, userType: 'user' } }
    ]
  },
  { 
    path: '/admin', 
    name: 'admin', 
    component: AW,
    meta: { requiresAuth: true, userType: 'admin' },
    redirect: '/admin/user-management',
    children: [
      { path: '/admin/user-management', name: 'userManagement', component: UserManagement, meta: { requiresAuth: true, userType: 'admin' } },
      { path: '/admin/logs', name: 'logViewer', component: LogViewer, meta: { requiresAuth: true, userType: 'admin' } },
      { path: '/admin/analytics', name: 'dataAnalysis', component: DataAnalysis, meta: { requiresAuth: true, userType: 'admin' } }
    ]
  },
  { path: '/', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userType = localStorage.getItem('userType')
  
  // 如果访问登录页面且已登录，自动跳转到对应页面
  if (to.path === '/login' && token) {
    if (userType === 'admin') {
      next('/admin')
    } else {
      next('/user')
    }
    return
  }
  
  // 需要认证的页面
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/login')
      return
    }
    
    // 检查用户类型权限
    if (to.meta.userType && to.meta.userType !== userType) {
      // 用户类型不匹配，跳转到对应页面
      if (userType === 'admin') {
        next('/admin')
      } else {
        next('/user')
      }
      return
    }
  }
  
  next()
})

export default router;