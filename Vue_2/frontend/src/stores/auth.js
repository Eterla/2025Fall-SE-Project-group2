import { reactive } from 'vue';
import axios from '../axios'; 

// 全局认证状态管理
const auth = reactive({
  user: null, // { id, username, email, ... }
  token: localStorage.getItem('access_token') || null, // JWT 令牌
  get isLoggedIn() { return !!this.token; }
});

// 初始化：如果有 token，尝试拉取用户信息（异步）
async function init() {
  console.log('初始化认证状态，当前 token:', auth.token);
  
  if (auth.token) {
    // 如果有 token，也尝试从 localStorage 恢复用户信息
    const storedUser = localStorage.getItem('user_info');
    if (storedUser) {
      try {
        auth.user = JSON.parse(storedUser);
        console.log('从 localStorage 恢复用户信息:', auth.user);
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    }
    
    try {
      // 验证 token 是否还有效
      const res = await axios.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${auth.token}` }
      });
      auth.user = res.data.user || res.data; // 根据后端返回结构
      // 更新 localStorage 中的用户信息
      localStorage.setItem('user_info', JSON.stringify(auth.user));
      console.log('Token 验证成功，用户信息:', auth.user);
    } catch (err) {
      console.error('Token 验证失败:', err);
      // token 无效或请求失败 -> 清除
      logout();
    }
  }
}

// 设置认证信息
// 使用场景：登录成功后调用
function setAuth(token, user) {
  console.log('设置认证信息:', { token, user });
  
  auth.token = token;
  auth.user = user || null;
  
  if (token) {
    localStorage.setItem('access_token', token);
    if (user) {
      localStorage.setItem('user_info', JSON.stringify(user));
    }
  } else {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
  }
  
  console.log('认证状态已更新:', auth);
}

function logout() {
  console.log('执行登出操作');
  
  auth.token = null;
  auth.user = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_info');
  
  console.log('登出完成，当前状态:', auth);
}

// 导出认证状态和方法
export default {
  auth,
  init,
  setAuth,
  logout
};