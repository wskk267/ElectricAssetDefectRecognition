// src/axios.js

import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://10.100.136.251:8090', // 改为本地地址，方便开发测试
  timeout: 300000, // 增加超时时间到5分钟，支持长视频处理
});

export default axiosInstance;
