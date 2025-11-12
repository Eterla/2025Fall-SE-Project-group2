import axios from 'axios';

// 创建axios实例，配置基础URL和超时时间
const instance = axios.create({
  baseURL: '',
  timeout: 5000
});

// 请求拦截器：添加日志和令牌
instance.interceptors.request.use(config => {
  console.log('请求拦截器 - 请求配置:', config);
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('请求拦截器 - 添加 Authorization 头:', config.headers.Authorization);
  }
  return config;
}, error => {
  console.error('请求拦截器 - 请求错误:', error);
  return Promise.reject(error);
});

// 响应拦截器：添加日志和错误处理
instance.interceptors.response.use(response => {
  console.log('响应拦截器 - 响应数据:', response);
  return response;
}, error => {
  console.error('响应拦截器 - 响应错误:', error);
  return Promise.reject(error);
});

export default instance;