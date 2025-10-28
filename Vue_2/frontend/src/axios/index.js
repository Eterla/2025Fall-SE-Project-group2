import axios from 'axios';

const instance = axios.create({
  baseURL: '/api',
  timeout: 5000
});

// 请求拦截器：添加token
instance.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器：处理错误
instance.interceptors.response.use(
  response => response.data,
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
