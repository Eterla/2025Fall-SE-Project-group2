<template>
  <div class="container">
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- 商品不存在提示 -->
    <div v-if="!loading && !item" class="text-center py-5">
      <h3>商品不存在或已被删除</h3>
      <router-link to="/" class="btn btn-primary mt-3">返回首页</router-link>
    </div>

    <!-- 商品详情 -->
    <div v-if="!loading && item" class="row mt-4">
      <!-- 商品图片 -->
      <div class="col-md-6">
        <img 
          :src="item.imagePath ? `/images/${item.imagePath}` : '/images/default.jpg'" 
          class="img-fluid rounded" 
          :alt="item.title"
        >
      </div>

      <!-- 商品信息 -->
      <div class="col-md-6">
        <h2 class="mb-3">{{ item.title }}</h2>
        <p class="text-danger fs-3 mb-4">¥{{ item.price }}</p>

        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">商品描述</h5>
            <p class="card-text">{{ item.description }}</p>
            <hr>
            <p class="card-text">
              <small class="text-muted">发布时间：{{ item.createdAt }}</small>
            </p>
            <p class="card-text">
              <small class="text-muted">状态：{{ item.status === 'available' ? '可交易' : '已售出' }}</small>
            </p>
          </div>
        </div>

        <!-- 卖家信息 -->
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">卖家信息</h5>
            <p class="card-text">用户名：{{ item.seller_name }}</p>
            <!-- 登录后显示聊天按钮 -->
            <button 
              class="btn btn-primary me-2" 
              @click="goToChat"
              v-if="isLogin && item.seller_id !== currentUserId"
            >
              联系卖家
            </button>
          </div>
        </div>

        <!-- 收藏按钮（登录后显示） -->
        <button 
          class="btn btn-outline-primary" 
          @click="toggleFavorite"
          v-if="isLogin"
        >
          <i class="bi" :class="isFavorite ? 'bi-heart-fill text-danger' : 'bi-heart'"></i>
          {{ isFavorite ? '取消收藏' : '收藏商品' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '@/axios'

export default {
  data() {
    return {
      loading: true,       // 加载状态
      item: null,          // 商品详情数据
      isLogin: false,      // 是否登录
      currentUserId: null, // 当前登录用户ID
      isFavorite: false    // 是否已收藏
    }
  },
  created() {
    // 页面加载时获取商品详情
    this.getItemDetail();
    // 检查登录状态
    this.checkLoginStatus();
  },
  methods: {
    // 获取商品详情
    async getItemDetail() {
      const itemId = this.$route.params.id; // 从路由参数中获取商品ID
      try {
        const response = await axios.get(`/items/${itemId}`);
        if (response.ok) {
          this.item = response.data;
          // 检查是否已收藏
          this.checkFavoriteStatus();
        } else {
          alert(response.data.message || '获取商品失败');
        }
      } catch (error) {
        console.error('获取商品详情失败:', error);
        alert('网络错误，请稍后再试');
      } finally {
        this.loading = false;
      }
    },

    // 检查登录状态
    checkLoginStatus() {
      const token = localStorage.getItem('access_token');
      const userInfo = localStorage.getItem('user_info');
      if (token && userInfo) {
        this.isLogin = true;
        this.currentUserId = JSON.parse(userInfo).id;
      }
    },

    // 检查是否已收藏
    async checkFavoriteStatus() {
      if (!this.isLogin || !this.item) return;
      try {
        const response = await axios.get(`/favorites/check?item_id=${this.item.id}`);
        this.isFavorite = response.data.is_favorite;
      } catch (error) {
        console.error('检查收藏状态失败:', error);
      }
    },

    // 切换收藏状态
    async toggleFavorite() {
      try {
        if (this.isFavorite) {
          // 取消收藏
          await axios.delete(`/favorites/${this.item.id}`);
          this.isFavorite = false;
          alert('取消收藏成功');
        } else {
          // 收藏商品
          await axios.post('/favorites', { item_id: this.item.id });
          this.isFavorite = true;
          alert('收藏成功');
        }
      } catch (error) {
        console.error('切换收藏状态失败:', error);
        alert('操作失败，请稍后再试');
      }
    },

    // 跳转到聊天页面
    goToChat() {
      this.$router.push({
        name: 'ChatDetail',
        params: {
          otherUserId: this.item.seller_id,
          itemId: this.item.id
        }
      });
    }
  }
}
</script>

<style>
/* 商品详情页图片样式 */
.img-fluid {
  max-height: 500px;
  object-fit: contain;
}
</style>