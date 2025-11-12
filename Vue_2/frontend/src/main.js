import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import authStore from './stores/auth';
import axios from './axios';

// 创建Vue应用
const app = createApp(App);

// 全局注册axios
app.config.globalProperties.$axios = axios;
app.config.globalProperties.$auth = authStore.auth;

// 注册全局消息提示
app.config.globalProperties.$message = {
  success(message) {
    alert(message);
  },
  error(message) {
    alert(message);
  }
};

// 注册全局确认对话框
app.config.globalProperties.$confirm = function(message, title = '提示', options = {}) {
  return new Promise((resolve) => {
    if (confirm(`${title}\n${message}`)) {
      resolve(options.confirmButtonText === '确定');
    } else {
      resolve(false);
    }
  });
};

// 初始化 auth（若有 token 自动尝试获取用户信息）
authStore.init();
// 使用路由
app.use(router);

// 挂载应用
app.mount('#app');
