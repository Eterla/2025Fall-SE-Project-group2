<template>
  <div class="container">
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <div v-if="!loading">
      <!-- 用户信息卡片 -->
      <div class="card mb-4">
        <div class="card-header bg-red text-white">
          <h3>个人信息</h3>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-2">
              <!-- 头像（默认用用户名首字母） -->
              <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center fs-3" style="width: 100px; height: 100px;">
                {{ userInfo.username.charAt(0).toUpperCase() }}
              </div>
            </div>
            <div class="col-md-10">
              <h4>{{ userInfo.username }}</h4>
              <p class="text-muted">注册时间：{{ userInfo.createdAt }}</p>
              <button class="btn btn-outline-primary" @click="editProfile">编辑资料</button>
              <button class="btn btn-outline-danger ms-2" @click="logout">退出登录</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 我的商品列表 -->
      <div class="card">
        <div class="card-header bg-red text-white d-flex justify-content-between align-items-center">
          <h3>我的商品</h3>
          <router-link to="/publish" class="btn btn-light">发布新商品</router-link>
        </div>
        <div class="card-body">
          <!-- 没有商品时显示 -->
          <div v-if="myItems.length === 0" class="text-center py-5">
            <p class="text-muted">你还没有发布任何商品</p>
            <router-link to="/publish" class="btn btn-red">去发布</router-link>
          </div>

          <!-- 商品列表 -->
          <div class="row" v-if="myItems.length > 0">
            <div class="col-md-4 mb-4" v-for="item in myItems" :key="item.id">
              <div class="card item-card">
                <img 
                  :src="item.imagePath ? `/images/${item.imagePath}` : '/images/default.jpg'" 
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
                  <div class="d-flex gap-2">
                    <router-link :to="`/item/${item.id}`" class="btn btn-outline-primary flex-1">查看</router-link>
                    <button class="btn btn-outline-warning flex-1" @click="editItem(item.id)">编辑</button>
                    <button 
                      class="btn btn-outline-danger flex-1" 
                      @click="changeStatus(item.id, item.status)"
                    >
                      {{ item.status === 'available' ? '下架' : '上架' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
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
      userInfo: {},        // 用户信息
      myItems: []          // 我的商品列表
    }
  },
  created() {
    // 页面加载时获取用户信息和商品列表
    this.getUserInfo();
    this.getMyItems();
  },
  methods: {
    // 获取用户信息
    async getUserInfo() {
      try {
        // 从本地存储获取用户信息（登录时保存的）
        const userInfoStr = localStorage.getItem('user_info');
        if (userInfoStr) {
          this.userInfo = JSON.parse(userInfoStr);
        } else {
          // 如果本地没有，调用接口获取（实际项目中需要后端接口支持）
          const response = await axios.get('/auth/me');
          if (response.ok) {
            this.userInfo = response.data;
            localStorage.setItem('user_info', JSON.stringify(this.userInfo)); // 保存到本地
          }
        }
      } catch (error) {
        console.error('获取用户信息失败:', error);
        alert('获取用户信息失败，请刷新页面重试');
      }
    },

    // 获取我的商品列表
    async getMyItems() {
      try {
        // 调用后端接口获取当前用户发布的商品
        const response = await axios.get('/items/my');
        if (response.ok) {
          this.myItems = response.data;
        } else {
          alert(response.data.message || '获取商品列表失败');
        }
      } catch (error) {
        console.error('获取我的商品失败:', error);
        // 暂时用模拟数据显示（后端接口未实现时）
        this.myItems = [
          {
            id: 1,
            title: '我的测试商品1',
            price: 199,
            imagePath: 'default.jpg',
            status: 'available'
          },
          {
            id: 2,
            title: '我的测试商品2',
            price: 299,
            imagePath: '',
            status: 'sold'
          }
        ];
      } finally {
        this.loading = false;
      }
    },

    // 编辑个人资料（预留方法）
    editProfile() {
      alert('编辑资料功能待实现');
      // 实际项目中可跳转到编辑页面，或弹出编辑模态框
    },

    // 退出登录
    logout() {
      if (confirm('确定要退出登录吗？')) {
        // 清除本地存储的登录信息
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        // 跳转到登录页
        this.$router.push('/login');
        // 刷新页面
        window.location.reload();
      }
    },

    // 编辑商品（跳转到编辑页面，预留）
    editItem(itemId) {
      alert(`编辑商品 ${itemId}（功能待实现）`);
      // 实际项目中可跳转到编辑页面：this.$router.push(`/edit-item/${itemId}`)
    },

    // 改变商品状态（上架/下架）
    async changeStatus(itemId, currentStatus) {
      const newStatus = currentStatus === 'available' ? 'sold' : 'available';
      const actionText = newStatus === 'available' ? '上架' : '下架';

      if (!confirm(`确定要${actionText}该商品吗？`)) {
        return;
      }

      try {
        // 调用后端接口修改商品状态
        const response = await axios.patch(`/api/items/${itemId}/status`, {
          status: newStatus
        });

        if (response.ok) {
          alert(`商品已${actionText}成功`);
          // 重新获取商品列表
          this.getMyItems();
        } else {
          alert(response.data.message || '操作失败');
        }
      } catch (error) {
        console.error('修改商品状态失败:', error);
        alert('网络错误，请稍后再试');
      }
    }
  }
}
</script>

<style>
/* 头像样式 */
.avatar {
  font-weight: bold;
}
</style>