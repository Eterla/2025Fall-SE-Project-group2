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
            <!-- 添加忘记密码链接 -->
            <p class="text-center mt-2">
              <a href="#" @click.prevent="showForgotPassword">忘记密码？</a>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 忘记密码弹窗 -->
    <div v-if="showForgotPasswordModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">找回密码</h5>
          <button type="button" class="btn-close" @click="closeModal"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleForgotPassword">
            <div class="mb-3">
              <label for="forgotUsername" class="form-label">用户名</label>
              <input 
                type="text" 
                class="form-control" 
                id="forgotUsername" 
                v-model="forgotData.username" 
                required
                placeholder="请输入您的用户名"
              >
            </div>
            <div class="mb-3">
              <label for="forgotEmail" class="form-label">邮箱</label>
              <input 
                type="email" 
                class="form-control" 
                id="forgotEmail" 
                v-model="forgotData.email" 
                required
                placeholder="请输入注册时使用的邮箱"
              >
            </div>
            <button type="submit" class="btn btn-red w-100" :disabled="loading">
              <span v-if="loading">处理中...</span>
              <span v-else>重置密码</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/axios'
import socketService from '@/services/SocketService'
import { useChatStore } from '@/stores/chat'

export default {
  data() {
    return {
      username: '',
      password: '',
      // 添加忘记密码相关数据
      showForgotPasswordModal: false,
      forgotData: {
        username: '',
        email: ''
      },
      loading: false
    }
  },
  methods: {
    async handleLogin() {
      try {
        const response = await api.post('/auth/login', {
          username: this.username,
          password: this.password
        });
        console.log('login response:', response);
        if (response.ok) {
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('user_info', JSON.stringify(response.data.user));
          console.log('login successful, token and user info saved.');
          
          socketService.connect(response.data.access_token)

          socketService.onNewMessage((msg) => {
            console.log('收到 new_message', msg)
            const chatStore = useChatStore()
            chatStore.addMessage(msg.data)
          })

          socketService.onUserTyping((data) => {
            console.log('收到 user_typing', data)
          })
          
          await this.$router.push('/');
          window.location.reload();
        } else {
          alert(response.error?.message || '登录失败');
        }
      } catch (error) {
        console.error('登录请求失败:', error);
        if (error && error.ok === false && error.error) {
          alert(error.error.message || '登录失败');
        } else {
          alert('网络错误，请检查后端是否启动或控制台是否有错误信息');
        }
      }
    },
    
    // 显示忘记密码弹窗
    showForgotPassword() {
      this.showForgotPasswordModal = true;
      // 清空表单数据
      this.forgotData = {
        username: '',
        email: ''
      };
    },
    
    // 关闭弹窗
    closeModal() {
      this.showForgotPasswordModal = false;
      this.loading = false;
    },
    
    // 处理忘记密码请求
    async handleForgotPassword() {
      if (!this.forgotData.username || !this.forgotData.email) {
        alert('请输入用户名和邮箱');
        return;
      }
      
      this.loading = true;
      
      try {
        // 调用忘记密码接口
        const response = await api.post('/auth/checkforpasswd', {
          username: this.forgotData.username,
          email: this.forgotData.email
        });
        
        if (response.ok && response.data) {
          // 显示临时密码并提示用户登录后修改
          alert(`用户名：${response.data.username}\n临时密码：${response.data.temporaryPassword}\n\n${response.data.message || '请使用临时密码登录后尽快修改密码。'}`);
          this.closeModal();
        } else {
          alert(response.error?.message || '重置失败');
        }
      } catch (error) {
        console.error('忘记密码请求失败:', error);
        if (error && error.ok === false && error.error) {
          alert(error.error.message || '重置失败');
        } else {
          alert('网络错误，请稍后重试');
        }
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
}

.modal-body {
  padding: 1rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  opacity: 0.5;
}

.btn-close:hover {
  opacity: 0.75;
}

/* 忘记密码链接样式 */
.text-center.mt-2 a {
  color: #666;
  text-decoration: none;
}

.text-center.mt-2 a:hover {
  color: #dc3545;
  text-decoration: underline;
}

/* 禁用按钮样式 */
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>