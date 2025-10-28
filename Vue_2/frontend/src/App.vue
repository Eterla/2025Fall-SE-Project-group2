<template>
  <div id="app">
    <!-- 导航栏组件（后面会创建） -->
    <Navbar />
    <!-- 页面内容会在这里显示 -->
    <router-view />
  </div>
</template>

<script>
// 先导入导航栏组件（后面会创建，现在可能报错，暂时忽略）
import Navbar from './components/Navbar.vue'

export default {
  components: {
    Navbar
  }
}
</script>

<style>
/* 引入 Bootstrap 样式 */
@import 'bootstrap/dist/css/bootstrap.min.css';

/* 复制 base.html 中的自定义样式 */
.item-card {
  transition: transform 0.2s;
}
.item-card:hover {
  transform: translateY(-5px);
}
.item-image {
  height: 200px;
  object-fit: cover;
}
.nav-link.active {
  font-weight: bold;
}

/* 给页面内容加边距（对应 base.html 的 container mt-4） */
.container {
  margin-top: 1rem;
}
</style>