<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white">
            <h3 class="text-center">用户注册</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleRegister">
              <!-- 用户名 -->
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="username" 
                  v-model="username" 
                  required
                  placeholder="请输入用户名"
                >
              </div>

              <!-- 密码 -->
              <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="password" 
                  v-model="password" 
                  required
                  placeholder="请输入密码"
                >
              </div>

              <!-- 确认密码 -->
              <div class="mb-3">
                <label for="confirmPassword" class="form-label">确认密码</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="confirmPassword" 
                  v-model="confirmPassword" 
                  required
                  placeholder="请再次输入密码"
                >
                <!-- 密码不一致提示 -->
                <p class="text-danger mt-1" v-if="password !== confirmPassword && confirmPassword">
                  两次密码输入不一致
                </p>
              </div>

              <!-- 邮箱（可选，根据旧模板是否有） -->
              <div class="mb-3">
                <label for="email" class="form-label">邮箱（选填）</label>
                <input 
                  type="email" 
                  class="form-control" 
                  id="email" 
                  v-model="email" 
                  placeholder="请输入邮箱"
                >
              </div>

              <button type="submit" class="btn btn-primary w-100" :disabled="password !== confirmPassword">
                注册
              </button>
            </form>
            <p class="text-center mt-3">
              已有账号？<router-link to="/login">立即登录</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      password: '',
      confirmPassword: '',
      email: ''
    }
  },
  methods: {
    async handleRegister() {
      if (this.password !== this.confirmPassword) {
        alert('两次密码不一致');
        return;
      }

      // 使用 main.js 全局注入的 this.$axios，避免路径 import 错误
      const axios = this.$axios;

      // 明确写出要请求的相对路径（以 /api 开头以触发 devServer proxy）
      const url = '/api/auth/register';
      console.log('[Register] 准备发送注册请求', url, {
        username: this.username,
        email: this.email
      });
      console.log('[Register] axios defaults baseURL:', axios.defaults.baseURL);

      try {
        const response = await axios.post(url, {
          username: this.username,
          password: this.password,
          email: this.email
        }
        );
        console.log('注册响应:', response && response.data ? response.data : response);
        console.log('response:', response);

        if (response.data && response.ok) {
          alert('注册成功，请登录');
          this.$router.push('/login');
        } else {
          alert((response.data && response.data.message) || '注册失败');
        }
      } catch (error) {
        console.error('注册请求失败:', error);
        // 如果 error.response 存在，可以打印更多信息
        if (error.response) {
          console.error('错误响应体:', error.response.status, error.response.data);
          alert('请求错误: ' + error.response.status);
        } else {
          alert('网络错误，请稍后再试');
        }
      }
    }
  }
}
</script>