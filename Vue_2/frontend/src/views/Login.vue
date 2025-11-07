<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white">
            <h3 class="text-center">用户登录</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="username" 
                  v-model="username" 
                  required
                >
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="password" 
                  v-model="password" 
                  required
                >
              </div>
              <button type="submit" class="btn btn-primary w-100">登录</button>
            </form>
            <p class="text-center mt-3">
              还没有账号？<router-link to="/register">立即注册</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import authStore from '../stores/auth'; // 引入认证状态管理
export default {
  data() {
    return {
      username: '',
      password: ''
    }
  },
  methods: {
    async handleLogin() { // 添加async关键字，支持await
      // 使用 main.js 全局注入的 this.$axios，避免路径 import 错误
      const axios = this.$axios;
      try {
        // 调用后端登录接口（与api.md匹配的地址）
        const response = await axios.post('/api/auth/login', {
          username: this.username,
          password: this.password
        });
        console.log('登录响应:', response);
        // 处理登录成功（根据api.md的响应格式）
        if (response.data.ok) {
          console.log('登录成功:', response.data);
          const token = response.data.data.access_token;
          const user = response.data.data.user;
          // 保存后端返回的token和用户信息到localStorage
          localStorage.setItem('access_token', token);
          localStorage.setItem('user_info', JSON.stringify(user));

          // 更新 store（import authStore）
          authStore.setAuth(token, user);
          // 跳转到首页或其他受保护的页面
          this.$router.push('/');
  
        } else {
          // 后端返回失败信息（如用户名密码错误）
          alert(response.error.message || '登录失败');
        }
      } catch (error) {
        // 处理网络错误或服务器异常
        console.error('登录请求失败:', error);
        if (error.response) {
          // 后端返回的错误（如401 Unauthorized）
          alert(error.response.error.message || '用户名或密码错误');
        } else {
          alert('网络错误，请检查后端是否启动');
        }
      }
    }
  }
}
</script>