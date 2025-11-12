<template>
  <div class="container">
    <!-- 搜索框 -->
    <div class="mb-4">
      <div class="d-flex">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索商品..." 
          class="form-control me-2"
        >
        <button @click="handleSearch" class="btn btn-primary">搜索</button>
      </div>
    </div>

    <!-- 商品列表 -->
    <h2 class="mb-4">
      {{ searchQuery ? `搜索结果: ${searchQuery}` : '最新商品' }}
    </h2>
    
    <!-- 加载状态 -->
    <div class="text-center my-4" v-if="loading">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
    </div>

    <div class="row" v-else>
      <!-- 循环显示商品 -->
      <div class="col-md-4 mb-4" v-for="item in items" :key="item.id">
        <div class="card item-card">
          <!-- 商品图片 -->
          <img 
            :src="item.imagePath ? `/images/${item.imagePath}` : '/images/default.jpg'" 
            class="card-img-top item-image" 
            :alt="item.title"
          >
          <div class="card-body">
            <h5 class="card-title">{{ item.title }}</h5>
            <p class="card-text text-danger font-weight-bold">¥{{ item.price }}</p>
            <p class="card-text text-muted" style="font-size: 0.9rem;">{{ item.createdAt }}</p>
            <router-link :to="`/item/${item.id}`" class="btn btn-primary w-100">查看详情</router-link>
          </div>
        </div>
      </div>

      <!-- 没有商品时显示 -->
      <div class="col-12 text-center" v-if="items.length === 0">
        <p class="text-muted">暂无商品</p>
      </div>
    </div>
  </div>
</template>

<script>
// 导入axios实例
import api from '@/axios'

export default {
  data() {
    return {
      searchQuery: '', // 搜索关键词
      items: [], // 从后端获取的商品数据
      loading: false // 加载状态
    }
  },
  mounted() {
    // 组件挂载时获取商品列表
    this.fetchItems();
  },
  methods: {
    async fetchItems() {
      this.loading = true;
      try {
        const response = await api.get('/items');
        if (response.ok) {
          this.items = response.data;
          console.log('商品列表加载成功:', this.items);
        } else {
          console.error('获取商品列表失败:', response.data.error?.message);
          alert('获取商品列表失败');
        }
      } catch (error) {
        console.error('获取商品列表请求失败:', error);
        alert('网络错误，请检查后端是否启动');
      } finally {
        this.loading = false;
      }
    },
    handleSearch() {
      // 搜索逻辑（后面对接后端）
      console.log('搜索:', this.searchQuery);
    }
  }
}
</script>