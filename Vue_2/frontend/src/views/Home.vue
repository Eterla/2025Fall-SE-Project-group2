<template>
  <div class="container-fluid p-0">
    <!-- 轮播图区域 -->
    <div id="carouselExampleIndicators" class="carousel slide" data-bs-ride="carousel">
      <!-- 轮播内容 -->
      <div class="carousel-inner">
        <!-- 第一张轮播图 -->
        <div class="carousel-item active school-bg">
          <img src="@/assets/images/bg1.png" class="d-block w-100" alt="校园风景">
        </div>
        <!-- 第二张轮播图 -->
        <div class="carousel-item school-bg">
          <img src="@/assets/images/bg2.png" class="d-block w-100" alt="二手市场">
        </div>
        <!-- 第三张轮播图 -->
        <div class="carousel-item school-bg">
          <img src="@/assets/images/bg3.png" class="d-block w-100" alt="交易场景">
        </div>
      </div>

      <!-- 轮播控制按钮 -->
      <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
      </button>
      <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
      </button>

      <!-- 轮播指示器 -->
      <div class="carousel-indicators">
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="0" class="active" aria-current="true" aria-label="Slide 1"></button>
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="1" aria-label="Slide 2"></button>
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="2" aria-label="Slide 3"></button>
      </div>

      <!-- 半透明覆盖层（移到轮播容器内，作为标题和搜索框的背景） -->
      <div class="bg-overlay"></div>

      <!-- 网站标题（绝对定位，在轮播图上方） -->
      <div class="site-title-container">
        <h1 class="site-title">博雅市集</h1>
        <p class="site-slogan">便捷安全的校园闲置物品交易市场</p>
      </div>

      <!-- 搜索框区域（保持在轮播图上方） -->
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

    <!-- 商品列表区域（保持不变） -->
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
              :src="item.image_path ? '/' + item.image_path.replace(/\\/g, '/') : require('@/assets/images/defaultPicture.png')"  
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
// 导入Bootstrap的Carousel组件（如果需要手动初始化）
import { Carousel } from 'bootstrap'

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
    // 初始化轮播组件（如果自动初始化不生效）
    setTimeout(() => {
      new Carousel(document.getElementById('carouselExampleIndicators'), {
        interval: 5000, // 自动轮播间隔时间（毫秒）
        wrap: true // 是否循环播放
      })
    }, 0)
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
/* 轮播图基础样式 */
.carousel {
  position: relative;
  height: 450px; /* 保持原有高度 */
  overflow: hidden;
}

.carousel-inner {
  height: 100%;
}

.carousel-item {
  height: 100%;
}

/* 轮播图片样式 */
.carousel-item img {
  height: 100%;
  object-fit: cover; /* 确保图片覆盖整个轮播区域 */
}

/* 半透明覆盖层（只作为标题和搜索框的背景） */
.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 1; /* 确保在轮播图上方，标题和搜索框下方 */
}

/* 网站标题容器 */
.site-title-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 2; /* 确保在覆盖层上方 */
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

/* 搜索框容器样式 - 调整定位 */
.search-container {
  position: absolute;
  bottom: 80px;
  left: 0;
  right: 0;
  max-width: 800px;
  margin: 0 auto;
  z-index: 2; /* 确保在覆盖层上方 */
}

/* 其他搜索框样式保持不变 */
.search-container .form-control {
  background-color: #fff !important;
  color: #333 !important;
  border: 1px solid #ced4da !important;
  padding: 0.3rem 1.5rem;
  font-size: 1rem;
  border-radius: 0.3rem 0 0 0.3rem !important;
}

.search-container .form-control::placeholder {
  color: #6c757d !important;
}

.search-container .btn-red {
  background-color: #900023 !important;
  color: #fff !important;
  border: none !important;
  padding: 0.5rem 2rem;
  font-size: 1rem;
  border-radius: 0 0.3rem 0.3rem 0 !important;
  font-weight: 500;
}

.search-container .form-control:focus {
  box-shadow: 0 0 0 0.25rem rgba(144, 0, 35, 0.25) !important;
  border-color: #900023 !important;
}
#carouselExampleIndicators .carousel-control-prev,
#carouselExampleIndicators .carousel-control-next {
  z-index: 10 !important; /* 确保这个值比 .bg-overlay 的 z-index 大 */
}

#carouselExampleIndicators .carousel-indicators {
  z-index: 10 !important; /* 同样提高指示器的层级 */
}

/* 可以检查一下覆盖层的 z-index，确保它小于10 */
#carouselExampleIndicators .bg-overlay {
  /* ... 其他样式 ... */
  z-index: 1; 
}
</style>