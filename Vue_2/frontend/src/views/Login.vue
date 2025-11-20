<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-red text-white">
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
              <button type="submit" class="btn btn-red w-100">登录</button>
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
// 导入axios（必须添加，否则无法发送请求）
import api from '@/axios'
import socketService from '@/services/SocketService'
import { useChatStore } from '@/stores/chat'

export default {
  data() {
    return {
      username: '',
      password: ''
    }
  },
  methods: {
    async handleLogin() { // 添加async关键字，支持await
      try {
        // 调用后端登录接口（与api.md匹配的地址）
        const response = await api.post('/auth/login', {
          username: this.username,
          password: this.password
        });
        console.log('login response:', response);
        // 处理登录成功（根据api.md的响应格式）
        if (response.ok) {
          // 保存后端返回的token和用户信息到localStorage
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('user_info', JSON.stringify(response.data.user));
          console.log('login successful, token and user info saved.');
          
          // 连接 websocket
          socketService.connect(response.data.access_token)

          // 注册一个新消息监听器
          socketService.onNewMessage((msg) => {
            console.log('收到 new_message', msg)
            const chatStore = useChatStore()
            chatStore.addMessage(msg.data)
          })

          // 注册一个监听正在输入事件的示例
          socketService.onUserTyping((data) => {
            console.log('收到 user_typing', data)
          })
          // 登录成功后跳转到首页
          await this.$router.push('/');
          // 刷新页面让全局状态生效（可选）
          window.location.reload();
        } else {
          // 后端返回失败信息（如用户名密码错误）
          alert(response.data.error?.message || '登录失败');
        }
      } catch (error) {
        // 处理网络错误或服务器异常
        console.error('登录请求失败:', error);
        if (error.response) {
          // 后端返回的错误（如401 Unauthorized）
          alert(error.response.data.error?.message || '用户名或密码错误');
        } else {
          alert('网络错误，请检查后端是否启动');
        }
      }
    }
  }
}
</script>