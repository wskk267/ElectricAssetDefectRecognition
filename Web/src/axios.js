// src/axios.js

import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://10.100.136.251:8090', // 改为本地地址，方便开发测试
  timeout: 300000, // 增加超时时间到5分钟，支持长视频处理
});

// 请求拦截器：自动添加token
axiosInstance.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理认证错误
axiosInstance.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response && error.response.status === 401) {
      // 认证失败，清除本地token并跳转到登录页
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
