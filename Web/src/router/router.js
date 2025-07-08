

import { createRouter, createWebHistory } from 'vue-router';
import login from '../components/login.vue'
import UW1 from '../user/UW1.vue'
import ImageRecognition from '../user/ImageRecognition.vue'
import VideoRecognition from '../user/VideoRecognition.vue'
import UserProfile from '../user/UserProfile.vue'

const routes = [
  { path: '/login', name: 'login', component: login, meta: { requiresAuth: false } },
  { 
    path: '/', 
    name: 'home', 
    component: UW1,
    redirect: '/image-recognition',
    children: [
      { path: '/image-recognition', name: 'imageRecognition', component: ImageRecognition },
      { path: '/video-recognition', name: 'videoRecognition', component: VideoRecognition },
      { path: '/user-profile', name: 'userProfile', component: UserProfile }
    ]
  },
]
const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;