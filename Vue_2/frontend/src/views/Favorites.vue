<template>
  <div class="container">
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- 收藏列表标题 -->
    <h2 class="my-4">我的收藏</h2>

    <!-- 没有收藏时显示 -->
    <div v-if="!loading && favorites.length === 0" class="text-center py-5">
      <p class="text-muted">你还没有收藏任何商品</p>
      <router-link to="/" class="btn btn-red">去逛逛</router-link>
    </div>

    <!-- 收藏列表 -->
    <div class="row" v-if="!loading && favorites.length > 0">
      <div class="col-md-4 mb-4" v-for="item in favorites" :key="item.id">
        <div class="card item-card position-relative">
          <!-- 取消收藏按钮（悬浮显示） -->
          <button 
            class="btn btn-danger rounded-circle position-absolute top-2 right-2"
            style="width: 30px; height: 30px; padding: 0; display: none;"
            @click.stop="removeFavorite(item.id)"
          >
            <i class="bi bi-x"></i>
          </button>

          <!-- 商品图片 -->
          <img 
            :src="item.image_path ? '/' + item.image_path.replace(/\\/g, '/') : require('@/assets/images/defaultPicture.png')" 
            class="card-img-top item-image" 
            :alt="item.title"
          >
          
          <div class="card-body">
            <h5 class="card-title">{{ item.title }}</h5>
            <p class="card-text text-danger font-weight-bold">¥{{ item.price }}</p>
            <p class="card-text">
              <span class="badge" :class="item.status === 'available' ? 'bg-success' : 'bg-secondary'">
                {{ item.status === 'available' ? '可交易' : '已售出' }}
              </span>
            </p>
            <p class="card-text text-muted" style="font-size: 0.9rem;">
              卖家：{{item.seller?.username}}
            </p>
            <router-link :to="`/item/${item.id}`" class="btn btn-red w-100">查看详情</router-link>
          </div>
        </div>
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
      favorites: []        // 收藏列表数据
    }
  },
  created() {
    // 页面加载时获取收藏列表
    this.getFavorites();
  },
  mounted() {
    // 实现鼠标悬停显示“取消收藏”按钮
    const cards = document.querySelectorAll('.item-card');
    cards.forEach(card => {
      card.addEventListener('mouseenter', () => {
        card.querySelector('button').style.display = 'flex';
      });
      card.addEventListener('mouseleave', () => {
        card.querySelector('button').style.display = 'none';
      });
    });
  },
  methods: {
    // 获取收藏列表
    async getFavorites() {
      try {
        // 调用后端接口获取收藏列表
        const response = await axios.get('/favorites');
        if (response.ok) {
          this.favorites = response.data;
        } else {
          alert(response.data.message || '获取收藏列表失败');
        }
      } catch (error) {
        console.error('获取收藏列表失败:', error);
        // 后端接口未实现时，用模拟数据显示
        this.favorites = [
          {
            id: 1,
            title: '收藏的商品1',
            price: 150,
            imagePath: 'default.jpg',
            status: 'available',
            seller: { username: '卖家A' }
          },
          {
            id: 2,
            title: '收藏的商品2',
            price: 300,
            imagePath: '',
            status: 'available',
            seller: { username: '卖家B' }
          }
        ];
      } finally {
        this.loading = false;
      }
    },

    // 取消收藏
    async removeFavorite(itemId) {
      if (!confirm('确定要取消收藏这个商品吗？')) {
        return;
      }

      try {
        // 调用后端接口取消收藏
        const response = await axios.delete(`/favorites/${itemId}`);
        if (response.ok) {
          alert('取消收藏成功');
          // 重新获取收藏列表
          this.getFavorites();
        } else {
          alert(response.data.message || '取消收藏失败');
        }
      } catch (error) {
        console.error('取消收藏失败:', error);
        alert('网络错误，请稍后再试');
      }
    }
  }
}
</script>

<style>
/* 取消收藏按钮样式优化 */
.item-card button {
  align-items: center;
  justify-content: center;
  opacity: 0.8;
  z-index: 10;
}
.item-card button:hover {
  opacity: 1;
}
</style>