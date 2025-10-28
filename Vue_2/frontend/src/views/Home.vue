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
    <div class="row">
      <!-- 循环显示商品（暂时用模拟数据） -->
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
export default {
  data() {
    return {
      searchQuery: '', // 搜索关键词
      // 模拟商品数据（后面会替换为后端请求）
      items: [
        {
          id: 1,
          title: '二手手机',
          price: 1000,
          imagePath: 'default.jpg',
          createdAt: '2023-10-01'
        },
        {
          id: 2,
          title: '笔记本电脑',
          price: 3000,
          imagePath: '', // 无图片时用默认图
          createdAt: '2023-10-02'
        }
      ]
    }
  },
  methods: {
    handleSearch() {
      // 搜索逻辑（后面对接后端）
      console.log('搜索:', this.searchQuery);
    }
  }
}
</script>