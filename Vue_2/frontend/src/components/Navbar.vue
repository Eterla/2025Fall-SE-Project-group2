<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container">
      <!-- 网站标题 -->
      <router-link class="navbar-brand" to="/">博雅市集</router-link>

      <!-- 移动端菜单按钮 -->
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>

      <!-- 导航菜单 -->
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/">首页</router-link>
          </li>

          <!-- 登录后显示的菜单 -->
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link" to="/publish">发布商品</router-link>
          </li>
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link" to="/user-center">个人中心</router-link>
          </li>
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link" to="/favorites">我的收藏</router-link>
          </li>
          <li class="nav-item" v-if="isLogin">
            <router-link class="nav-link" to="/messages">消息</router-link>
          </li>
        </ul>

        <!-- 登录/注册按钮 -->
        <div class="d-flex align-items-center">
          <span class="navbar-text me-3" v-if="isLogin">欢迎, {{ username }}</span>

          <!-- 登出用按钮（不要用 to="/logout" 以便先清理本地状态） -->
          <button class="btn btn-outline-danger me-2" v-if="isLogin" @click="handleLogout">
            退出
          </button>

          <router-link class="btn btn-outline-primary me-2" to="/login" v-if="!isLogin">登录</router-link>
          <router-link class="btn btn-primary" to="/register" v-if="!isLogin">注册</router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import authStore from '@/stores/auth';

export default {
  name: 'Navbar',
  data() {
    return {
      // 本地状态，用于强制重新渲染
      authState: authStore.auth,
      refreshKey: 0
    }
  },
  computed: {
    // 是否已登录
    isLogin() {
      // 添加 refreshKey 确保响应式更新
      this.refreshKey;
      
      // 多重检查确保登录状态正确
      const storeToken = this.authState.token;
      const localToken = localStorage.getItem('access_token');
      
      console.log('Store token:', storeToken);
      console.log('Local token:', localToken);
      console.log('Auth state:', this.authState);
      console.log('isLogin result:', !!(storeToken || localToken));
      return !!(storeToken || localToken);
    },
    // 当前用户名
    username() {
      this.refreshKey; // 确保响应式更新
      
      const user = this.authState.user || JSON.parse(localStorage.getItem('user_info') || '{}');
      return user ? user.username : '';
    }
  },
  mounted() {
    // 组件挂载时同步状态
    this.syncAuthState();
    
    // 监听localStorage变化
    window.addEventListener('storage', this.handleStorageChange);
    
    // 监听路由变化，确保状态同步
    this.$router.afterEach(() => {
      this.syncAuthState();
    });
  },
  beforeUnmount() {
    // 清理事件监听器
    window.removeEventListener('storage', this.handleStorageChange);
  },
  methods: {
    // 同步认证状态
    syncAuthState() {
      const localToken = localStorage.getItem('access_token');
      const localUser = localStorage.getItem('user_info');
      
      if (localToken && !this.authState.token) {
        // 本地有token但store没有，恢复到store
        const user = localUser ? JSON.parse(localUser) : null;
        authStore.setAuth(localToken, user);
        this.forceUpdate();
      } else if (!localToken && this.authState.token) {
        // 本地没有token但store有，清除store
        authStore.logout();
        this.forceUpdate();
      }
    },
    
    // 处理localStorage变化
    handleStorageChange(e) {
      if (e.key === 'access_token' || e.key === 'user_info') {
        this.syncAuthState();
      }
    },
    
    // 强制更新组件
    forceUpdate() {
      this.refreshKey++;
      this.$forceUpdate();
    },
    
    // 处理登出
    handleLogout() {
      // 清理认证状态
      authStore.logout();
      
      // 清理本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      
      // 强制更新
      this.forceUpdate();
      
      // 跳转到首页
      this.$router.push('/');
    }
  }
}
</script>

<style scoped>
.navbar-text {
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>