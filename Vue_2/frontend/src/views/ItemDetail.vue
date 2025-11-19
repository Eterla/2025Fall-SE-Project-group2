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
      <router-link to="/" class="btn btn-red mt-3">返回首页</router-link>
    </div>

    <!-- 商品详情 -->
    <div v-if="!loading && item" class="row mt-4">
      <!-- 商品图片 -->
      <div class="col-md-6">
        <img 
          :src="item.imagePath ? '/' + item.imagePath.replace(/\\/g, '/') : require('@/assets/images/defaultPicture.png')"  
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

            <!-- 标签展示：使用 item.tags（getItemDetail 已规范化为数组） -->
            <div v-if="item.tags && item.tags.length" class="mt-3">
              <h6 class="mb-2">标签</h6>
              <div>
                <span 
                  v-for="(tag, idx) in item.tags" 
                  :key="idx" 
                  class="badge bg-secondary me-1"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 卖家信息 -->
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">卖家信息</h5>
            <p class="card-text">用户名：{{ item.seller_name }}</p>
            <!-- 登录后显示聊天按钮 -->
            <button 
              class="btn btn-red me-2" 
              @click="goToChat"
              v-if="isLogin && item.seller_id !== currentUserId"
            >
              联系卖家
            </button>
          </div>
        </div>

        <!-- 收藏按钮（登录后显示） -->
        <button 
          class="btn btn-outline-red" 
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
import dayjs from '@/utils/dayjs-plugins.js'
console.log('dayjs 是否加载成功:', typeof dayjs === 'function' ? '是' : '否', dayjs)

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
async getItemDetail() {
  const itemId = this.$route.params.id;
  try {
    const response = await axios.get(`/items/${itemId}`);
    console.log('getItemDetail response:', response);

    // 直接使用响应数据（后端直接返回商品对象）
    const respData = response.data;

    if (!respData) {
      console.warn('响应数据为空');
      alert('获取商品失败（无商品数据）');
      return;
    }
const rawTime = respData.createdAt || respData.created_at;
let formattedTime = '暂无时间';
if (rawTime) {
  try {
    // 直接按本地时区（北京时间）解析
    const dayjsObj = dayjs(rawTime);
    if (dayjsObj.isValid()) {
      // 格式化成本地时间字符串
      formattedTime = dayjsObj.format('YYYY-MM-DD HH:mm:ss');
      console.log('最终显示时间:', formattedTime); // 应该和 rawTime 一致
    } else {
      formattedTime = '时间格式无效';
    }
  } catch (error) {
    console.error('时间处理报错:', error);
    formattedTime = '时间解析失败';
  }
}


    // 规范化字段名（保持原逻辑）
    const normalized = {
      ...respData,
      imagePath: respData.imagePath || respData.image_path || '',
      //createdAt: respData.createdAt || respData.created_at || '',
      createdAt: formattedTime,
      id: respData.id || respData.item_id || respData.itemId || null,
      seller_id: respData.seller_id || respData.sellerId || respData.seller || null,
      seller_name: respData.seller_name || respData.sellerName || '',
      tags: Array.isArray(respData.tags)
        ? respData.tags
        : (typeof respData.tags === 'string' ? respData.tags.split(/[\s,;，,]+/).map(s => s.trim()).filter(Boolean) : [])
    };

    this.item = normalized;
    // 直接从响应数据中获取收藏状态
    this.isFavorite = !!respData.is_favorite || !!respData.isFavorite;

    console.log('解析后的 item:', this.item, 'isFavorite:', this.isFavorite);
  } catch (error) {
    console.error('获取商品详情失败:', error);
    alert('网络错误或解析错误，请查看控制台详情');
  } finally {
    this.loading = false;
  }
},
//更改

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