// src/axios.js

import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://localhost:8090', // 改为本地地址，方便开发测试
  timeout: 10000, // 增加超时时间到10秒
});

export default axiosInstance;
