<template>
  <div class="container-fluid p-0">
    <!-- 轮播图区域 -->
    <div id="carouselExampleIndicators" class="carousel slide" data-bs-ride="carousel">
      <div class="carousel-inner">
        <div class="carousel-item active school-bg">
          <img src="@/assets/images/bg1.png" class="d-block w-100" alt="校园风景">
        </div>
        <div class="carousel-item school-bg">
          <img src="@/assets/images/bg2.png" class="d-block w-100" alt="二手市场">
        </div>
        <div class="carousel-item school-bg">
          <img src="@/assets/images/bg3.png" class="d-block w-100" alt="交易场景">
        </div>
      </div>
      <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
      </button>
      <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
      </button>
      <div class="carousel-indicators">
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="0" class="active" aria-current="true" aria-label="Slide 1"></button>
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="1" aria-label="Slide 2"></button>
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="2" aria-label="Slide 3"></button>
      </div>
      <div class="bg-overlay"></div>
      <div class="site-title-container">
        <h1 class="site-title">博雅市集</h1>
        <p class="site-slogan">便捷安全的校园闲置物品交易市场</p>
      </div>
      <!-- 搜索框区域 -->
      <div class="search-container container">
        <div class="d-flex justify-content-center align-items-center">
          <!-- 搜索框 + 内置清空按钮 -->
          <div class="position-relative me-2" style="width: 400px;">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索商品..." 
              class="form-control ps-3 pe-8"
            >
            <!-- 清空按钮 -->
            <button 
              class="btn btn-sm text-muted position-absolute end-0 top-50 translate-middle-y me-2"
              v-if="searchQuery.trim()"
              @click="resetSearch"
              style="border: none; background: transparent; cursor: pointer; font-size: 12px;"
            >
              清空
            </button>
          </div>
          <!-- 搜索按钮 -->
          <button @click="handleSearch" class="btn btn-red me-2">搜索</button>
          <!-- 最新商品按钮：修复样式冲突（btn-red+btn-light冲突） -->
          <button 
            @click="resetSearch" 
            class="btn btn-red btn-light"
            v-if="searchQuery.trim()"
          >
            最新商品
          </button>
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

      <!-- 商品列表 -->
      <div class="row" v-else>
        <template v-if="Array.isArray(items) && items.length > 0">
          <div class="col-md-4 mb-4 d-flex align-items-stretch" v-for="item in items" :key="item.id">
            <div class="card item-card w-100">
            
              <img 
                :src="item.image_path ? '/' + item.image_path.replace(/\\/g, '/') : require('@/assets/images/defaultPicture.png')"  
                class="card-img-top item-image" 
                :alt="item.title"
              >
              <div class="card-body d-flex flex-column">
                <!-- 新增：标签区域 -->
                <div class="mb-2 d-flex gap-2 flex-wrap">
                <!-- 商品标签：拆分字符串→截取前5个→循环渲染独立标签 -->
                <span 
                  v-for="(tag, index) in getLimitedTags(item.tags)" 
                  :key="index"
                  class="tag-item"
                >
                  {{ tag }}
                </span>
              </div>

                <h5 class="card-title">{{ item.title }}</h5>
                <p class="card-text text-danger font-weight-bold">¥{{ item.price }}</p>
                <!-- 修正：后端字段是created_at，不是createdAt -->
                <p class="card-text text-muted" style="font-size: 0.9rem;">{{ item.created_at }}</p>
                <router-link :to="`/item/${item.id}`" class="btn btn-red w-100 mt-auto">查看详情</router-link>
              </div>
            </div>
          </div>
        </template>

        <!-- 无商品/无搜索结果提示 -->
        <div class="col-12 text-center py-5" v-if="Array.isArray(items) && items.length === 0">
          <p class="text-muted fs-5">{{ searchQuery.trim() ? '未找到匹配的商品' : '暂无商品' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 导入axios实例
import api from '@/axios'
// 导入Bootstrap的Carousel组件
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
    // 初始化轮播组件
    setTimeout(() => {
      new Carousel(document.getElementById('carouselExampleIndicators'), {
        interval: 5000,
        wrap: true
      })
    }, 0)
  },
  methods: {
    async fetchItems(searchKeyword = '') {
      this.loading = true;
      try {
        const params = searchKeyword ? { search: searchKeyword } : {};
        console.log('准备请求的参数:', params);
        console.log('请求URL:', api.defaults.baseURL + '/items' + (params.search ? '?search=' + params.search : ''));
        
        const response = await api.get('/items', { params });
        
        if (response.ok) {
          this.items = response.data; 
          console.log('商品数据加载成功:', this.items);
        } else {
          console.error('获取商品失败:', response.data.error?.message);
          alert('获取商品失败');
        }
      } 
    catch (error) {
      console.error('请求失败:', error);
      if (error.response) {
        if (error.response.status === 500) {
          alert('服务器内部错误，请联系后端修复');
        } else {
          alert(`请求失败，状态码: ${error.response.status}`);
        }
      } else {
        alert('网络错误，请检查后端是否启动');
      }
    } finally {
        this.loading = false;
      }
    },
    handleSearch() {
      console.log('原始searchQuery:', this.searchQuery);
      const keyword = this.searchQuery.trim();
      console.log('处理后的搜索关键词:', keyword);
      this.fetchItems(keyword);
    },
    resetSearch() {
      this.searchQuery = '';
      this.fetchItems();
    },
    getLimitedTags(tagsStr) {
    if (!tagsStr) return []; // 标签为空时返回空数组
    // 按空格拆分（对应发布时的tags.join(' ')），过滤空值（避免多余空格导致的空标签）
    const tagsArray = tagsStr.split(' ').filter(tag => tag.trim());
    // 截取前5个标签
    return tagsArray.slice(0, 5);
  }
  }
}
</script>

<style>
/* 轮播图基础样式 */
.carousel {
  position: relative;
  height: 450px;
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
  object-fit: cover;
}

/* 半透明覆盖层 */
.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 1;
}

/* 网站标题容器 */
.site-title-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 2;
}

.site-title {
  font-size: 3.8rem;
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
  max-width: 800px;
  margin: 0 auto;
  z-index: 2;
}

/* 搜索框样式 */
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

/* 轮播控制按钮层级 */
#carouselExampleIndicators .carousel-control-prev,
#carouselExampleIndicators .carousel-control-next {
  z-index: 10 !important;
}

#carouselExampleIndicators .carousel-indicators {
  z-index: 10 !important;
}

/* 商品卡片样式优化 */
.item-card {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.item-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.item-image {
  width: 100%;
  border-bottom: 1px solid #eee;
}
/* 新增：独立标签样式 */
.tag-item {
  background-color: #900023;
  color: white;
  padding: 4px 8px;
  font-size: 0.75rem;
  border-radius: 4px;
  white-space: nowrap; /* 防止标签文字换行 */
}
</style>