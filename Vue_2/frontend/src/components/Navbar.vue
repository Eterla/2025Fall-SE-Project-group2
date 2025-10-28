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
          
          <!-- 登录后显示的菜单（用 v-if 判断） -->
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
        <div class="d-flex">
          <span class="navbar-text me-3" v-if="isLogin">欢迎, {{ username }}</span>
          <router-link class="btn btn-outline-danger" to="/logout" v-if="isLogin">退出</router-link>
          
          <router-link class="btn btn-outline-primary me-2" to="/login" v-if="!isLogin">登录</router-link>
          <router-link class="btn btn-primary" to="/register" v-if="!isLogin">注册</router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      // 临时默认值，后面会对接登录状态
      isLogin: false,  // 是否登录
      username: ''     // 用户名
    }
  }
}
</script>