<template>
  <nav class="navbar navbar-expand-lg navbar-light custom-nav-bg">
    <div class="container">
      <!-- 网站标题 -->
      <router-link class="navbar-brand text-white font-weight-bold" to="/">博雅市集</router-link>
      
      <!-- 移动端菜单按钮 -->
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      
      <!-- 导航菜单 -->
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link text-white font-weight-normal px-3" to="/">首页</router-link>
          </li>
          
          <!-- 登录后显示的菜单（用 v-if 判断） -->
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link text-white font-weight-normal px-3" to="/publish">发布商品</router-link>
          </li>
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link text-white font-weight-normal px-3" to="/favorites">我的收藏</router-link>
          </li>
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link text-white font-weight-normal px-3 position-relative" to="/messages">
              消息
              <span v-if="unreadCount > 0" class="unread-badge" :data-count="unreadCount>99 ? '99plus' : ''">{{ unreadCount>99 ? '99+' : unreadCount }}</span>
            </router-link>
          </li>
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link text-white font-weight-normal px-3" to="/user-center">个人中心</router-link>
          </li>
        </ul>
        
        <!-- 登录/注册/退出按钮区域 -->
        <div class="d-flex align-items-center gap-2">
          <span class="navbar-text me-2 text-white d-none d-sm-block" v-if="isLogin">欢迎, {{ username }}</span>
          <router-link class="btn btn-sm btn-outline-light" to="/logout" v-if="isLogin">退出</router-link>

          <router-link class="btn btn-sm btn-outline-light" to="/login" v-if="!isLogin">登录</router-link>
          <router-link class="btn btn-sm btn-light text-nav-bg" to="/register" v-if="!isLogin">注册</router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import { useChatStore } from '@/stores/chat'
import socketService from '@/services/SocketService'
import axios from '@/axios'

export default {
  data() {
    return {
      isLogin: false,
      username: '',
      refreshTimer: null
    }
  },
  computed: {
    // 直接从 Pinia store 读取响应式的 totalUnread getter
    unreadCount() {
      const store = useChatStore()
      console.log("Navbar.vue unreadCount:", store.totalUnread)
      return Number(store.totalUnread || 0)
    }
  },
  mounted() {
    // 组件挂载时检查登录状态
    this.checkLoginStatus()
    
    // 监听登录状态变化
    window.addEventListener('storage', this.checkLoginStatus)
    window.addEventListener('login-status-changed', this.checkLoginStatus)
    // 触发一次以确保 store 已被初始化
    // 如果已登录，提前拉取会话数据以便在其他页面（比如首页）显示未读数
    const store = useChatStore()
    if (localStorage.getItem('access_token')) {
      this.loadConversations(store)
      // 也可以尝试建立 socket 连接以接收实时消息（若后端支持 token auth）
      try { socketService.connect(localStorage.getItem('access_token')) } catch (e) { console.warn('socket connect failed', e) }
      
      this.refreshTimer = null
      this._onNewMessage = () => {
        if (this.refreshTimer) return
        this.refreshTimer = setTimeout(() => {
          this.refreshTimer = null
          this.loadConversations(store)
        }, 300)
      }
      socketService.on('new_message', this._onNewMessage)
    }
  },
  beforeUnmount() {
    // 清理事件监听
    window.removeEventListener('storage', this.checkLoginStatus)
    window.removeEventListener('login-status-changed', this.checkLoginStatus)

    if (this.refreshTimer) clearTimeout(this.refreshTimer)
    if (this._onNewMessage) socketService.off('new_message', this._onNewMessage)
  },
  methods: {
    async loadConversations(store) {
      try {
        const res = await axios.get('/messages/conversations')
        if (res && res.ok) {
          const data = res.data
          const mapped = data.map(conv => ({
            id: conv.conversation_id,
            other_user_id: conv.other_user_id,
            other_username: conv.other_username,
            item_id: conv.item_id,
            last_message_time: conv.last_message_time,
            last_message_content: conv.last_message_content,
            unread_count: conv.unread_count
          }))
          store.sessions = mapped
        }
      } catch (e) {
        console.warn('Navbar: loadConversations failed', e)
      }
    },
    checkLoginStatus() {
      // 从 localStorage 读取登录状态（修改为与 Login.vue 一致的 key）
      const token = localStorage.getItem('access_token')  // 改为 access_token
      const userInfo = localStorage.getItem('user_info')  // 改为 user_info
      
      this.isLogin = !!token
      if (userInfo) {
        try {
          const user = JSON.parse(userInfo)
          this.username = user.username || user.name || ''  // 根据实际的用户信息结构获取用户名
        } catch (e) {
          this.username = ''
        }
      } else {
        this.username = ''
      }
      // 若刚刚登录，确保拉取会话以更新未读数
      if (this.isLogin) {
        try {
          const store = useChatStore()
          this.loadConversations(store)
        } catch (e) {
          console.warn('Navbar: loadConversations on login failed', e)
        }
      }
    }
  },
  watch: {
    $route() {
      this.checkLoginStatus()
    }
  }
}
</script>

<style>
  /* 为导航栏自定义背景颜色 */
  .custom-nav-bg {
    background-color: #900023 !important;
  }
  
  /* 导航链接 hover 效果优化 */
  .navbar-nav .nav-link:hover {
    color: rgba(255, 255, 255, 0.9) !important;
    opacity: 0.9;
  }

  /* 自定义注册按钮文字颜色，使其与导航栏背景色一致 */
  .text-nav-bg {
    color: #900023 !important;
  }

  /* 响应式调整：在超小屏幕上，让按钮区域垂直排列 */
  @media (max-width: 575.98px) {
    #navbarNav .d-flex {
      flex-direction: column;
      align-items: flex-start !important;
      margin-top: 1rem;
      gap: 0.5rem !important; /* 减小垂直间距 */
    }
    .navbar-text {
      margin-bottom: 0.5rem;
    }
  }

  /* unread badge：小白点，内部红色数字，定位到消息链接右上角 */
  .nav-link.position-relative { 
    position: relative;
  } 

  .unread-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    min-width: 18px;
    height: 18px;
    padding: 0 5px;               /* 两位数时可扩展宽度 */
    background: #ffffff;          /* 白色圆点背景 */
    color: #900023;               /* 红色数字 */
    font-weight: 700;
    font-size: 0.65rem;
    border-radius: 999px;         /* 完全圆形 */
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    border: 1px solid rgba(0,0,0,0.06);
    line-height: 1;
    text-align: center;
    pointer-events: none;         /* 不阻塞点击消息链接 */
    transform: translate(0, 0);
    z-index: 10;
  }

  /* 当显示 "99+" 时，内容由模板直接渲染，无需 ::after */
  .unread-badge[data-count="99plus"] {
    padding: 0 6px;
  }

  @media (max-width: 575.98px) {
    .unread-badge {
      min-width: 16px;
      height: 16px;
      font-size: 0.6rem;
      top: 3px;
      right: 3px;
      padding: 0 4px;
    }
  }

</style>