<template>
  <div class="container-fluid p-0">
    <!-- 导航栏下方的背景区域 -->
    <div class="school-bg">
      <div class="bg-overlay">
        <h1 class="site-title">博雅市集</h1>
        <p class="site-slogan">便捷安全的校园闲置物品交易市场</p>
      </div>

      <!-- 搜索框区域 -->
      <div class="search-container container">
        <div class="d-flex justify-content-center">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索商品..." 
            class="form-control me-2"
          >
          <button @click="handleSearch" class="btn btn-red">搜索</button>
        </div>
      </div>
    </div>

    <!-- 商品列表区域 -->
    <div class="container mt-5">
      <h2 class="mb-4">
        {{ searchQuery ? '搜索结果' : '最新商品' }}
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
              <router-link :to="`/item/${item.id}`" class="btn btn-red w-100">查看详情</router-link>
            </div>
          </div>
        </div>

        <!-- 没有商品时显示 -->
        <div class="col-12 text-center" v-if="items.length === 0">
          <p class="text-muted">暂无商品</p>
        </div>
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

<style>
.school-bg {
  width: 100%;
  height: 450px;
  background-image: url('@/assets/images/bg1.png');
  background-size: cover;
  background-position: center;
  position: relative;
}

.bg-overlay {
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
  text-align: center;
}

.site-title {
  font-size: 2.8rem;
  font-weight: bold;
  margin-bottom: 1rem;
  color: #fff !important;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.site-slogan {
  font-size: 1.4rem;
  color: #fff !important;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

/* 搜索框容器样式 */
.search-container {
  position: absolute;
  bottom: 80px;
  left: 0;
  right: 0;
  max-width: 800px; /* 宽度保持不变 */
  margin: 0 auto;
}

/* 搜索框输入框样式 - 减小高度 */
.search-container .form-control {
  background-color: #fff !important;
  color: #333 !important;
  border: 1px solid #ced4da !important;
  /* 减小上下内边距 (padding) 来降低高度 */
  padding: 0.3rem 1.5rem; /* 上/下 padding 从 0.9rem 改为 0.5rem */
  font-size: 1rem; /* 字体大小从 1.1rem 改为 1rem */
  border-radius: 0.3rem 0 0 0.3rem !important;
}

/* 搜索框占位符颜色 */
.search-container .form-control::placeholder {
  color: #6c757d !important;
}

/* 搜索按钮样式 - 同步减小高度 */
.search-container .btn-red {
  background-color: #900023 !important;
  color: #fff !important;
  border: none !important;
  /* 按钮的 padding 也需要同步减小，以保持视觉协调 */
  padding: 0.5rem 2rem; /* 上/下 padding 从 0.9rem 改为 0.5rem */
  font-size: 1rem; /* 字体大小从 1.1rem 改为 1rem */
  border-radius: 0 0.3rem 0.3rem 0 !important;
  font-weight: 500;
}

/* 搜索框聚焦时的边框高亮颜色 */
.search-container .form-control:focus {
  box-shadow: 0 0 0 0.25rem rgba(144, 0, 35, 0.25) !important;
  border-color: #900023 !important;
}
</style>