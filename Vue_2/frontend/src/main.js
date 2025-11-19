import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import './assets/css/global.css' // 路径根据实际文件位置调整
// 引入axios
import axios from './axios';

// 创建Vue应用
const app = createApp(App);

// 全局注册axios
app.config.globalProperties.$axios = axios;

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

// 使用路由
app.use(router);

// 挂载应用
app.mount('#app');
