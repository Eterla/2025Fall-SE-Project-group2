import axios from 'axios';

// 创建axios实例，配置基础URL和超时时间
const instance = axios.create({
  baseURL: '',
  timeout: 5000
});

// 请求拦截器：添加日志和令牌
instance.interceptors.request.use(cfg => {
  console.log('发送请求:', cfg.method?.toUpperCase(), cfg.url, cfg.data) // 添加请求日志
  const token = localStorage.getItem('access_token')
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`
  }
  return cfg
})

// 响应拦截器：处理错误
instance.interceptors.response.use(
  response => {
    console.log('收到响应:', response.status, response.config.url) // 添加响应日志
    return response.data
  },
  error => {
    // 处理401令牌过期等错误
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response.data);
  }
);

export default instance;
