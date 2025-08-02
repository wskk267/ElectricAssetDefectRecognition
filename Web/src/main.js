import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import Particles from 'vue3-particles'
import router from './router/router.js'
import axios from 'axios'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 导入通用样式
import './styles/common.css'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const axiosInstance = axios.create({
  baseURL: "http://10.100.136.251:8090",
  timeout: 10000
});

app.config.globalProperties.$axios = axiosInstance;
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.use(Particles).mount('#app')


