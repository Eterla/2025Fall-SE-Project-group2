<template>
    <div v-if="error" class="container mt-5">
      <div class="alert alert-danger" role="alert">
        登出失败: {{ error }}
      </div>
    </div>
</template>

<script>
import api from '@/axios'
import socketService from '@/services/SocketService'
import { useChatStore } from '@/stores/chat'

export default {
  name: 'Logout',
  data() {
    return {
      error: null
    }
  },
  mounted() {
    this.performLogout()
  },
  methods: {
    async performLogout() {
        console.log('Logging out...')
        const chatStore = useChatStore()
        try {
            // 尝试通知后端登出（若后端未实现也不影响本地登出）
            const res = await api.post('/auth/logout')
        
            if (res && res.ok === false) { // 后端返回失败响应，但是目前后端没有返回失败响应的情况
                this.error = res.error?.message || '服务器拒绝登出请求' 
            }
        } catch (e) {
            // 记录网络错误
            console.error('logout error:', e)
        } finally {

        // 断开 WebSocket 连接
        try { 
            socketService.disconnect() 
        } catch (e) {
            console.error('SocketService.disconnect error during logout:', e)
        }
        // 清理聊天状态
        chatStore.clearAll()

        // 本地清理并跳转到登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        console.log("Logout: localStorage cleared")
        // 通知其它 tab，其他 tab 监听在 storage 事件中
        try {
            localStorage.setItem('logout', Date.now().toString())
        } catch (e) {
            console.error('Failed to set logout timestamp:', e)
        }

        // 通知当前 tab 登录状态已改变， 当前 tab 监听在 login-status-changed 事件中
        window.dispatchEvent(new Event('login-status-changed'))

        // 使用 replace 避免返回历史记录
        this.$router.replace('/login').catch(()=>{})
        console.log('Logout: finished, local cleared')
      }
    },
  }
}
</script>