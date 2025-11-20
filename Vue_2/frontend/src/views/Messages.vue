<template>
  <div class="container">
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- 页面标题 -->
    <h2 class="my-4">我的消息</h2>

    <!-- 没有消息时显示 -->
    <div v-if="!loading && conversations.length === 0" class="text-center py-5">
      <p class="text-muted">你还没有任何消息</p>
      <router-link to="/" class="btn btn-red">去逛逛</router-link>
    </div>

    <!-- 消息列表 -->
    <div class="list-group" v-if="!loading && conversations.length > 0">
      <!-- 单个聊天会话 -->
      <div 
        class="list-group-item list-group-item-action d-flex gap-3 p-3 cursor-pointer"
        v-for="conv in conversations" 
        :key="conv.other_user_id"
        @click="goToChat(conv.other_user_id, conv.last_item_id)"
      >
        <!-- 对方头像（用用户名首字母） -->
        <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px; flex-shrink: 0;">
          {{ conv.other_username.charAt(0).toUpperCase() }}
        </div>

        <!-- 消息内容 -->
        <div class="flex-grow-1 min-w-0">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <h6 class="mb-0">{{ conv.other_username }}</h6>
            <small class="text-muted">{{ formatTime(conv.last_time) }}</small>
          </div>
          <p class="mb-0 text-truncate">
            {{ conv.last_sender === 'me' ? '我：' : '' }}{{ conv.last_content }}
          </p>
        </div>

        <!-- 未读消息提示 -->
        <span v-if="conv.unread_count > 0" class="badge bg-danger align-self-start">
          {{ conv.unread_count }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '@/axios'

export default {
  data() {
    return {
      loading: true,               // 加载状态
      conversations: []            // 消息会话列表
    }
  },
  created() {
    // 页面加载时获取消息列表
    this.getConversations();
  },
  methods: {
    // 获取消息会话列表
    async getConversations() {
      try {
        // 调用后端接口获取消息列表
        const response = await axios.get('/messages/conversations');
        if (response.ok) {
          this.conversations = response.data;
        } else {
          alert(response.data.message || '获取消息列表失败');
        }
      } catch (error) {
        console.error('获取消息列表失败:', error);
        // 后端接口未实现时，用模拟数据显示
        this.conversations = [
          {
            other_user_id: 2,
            other_username: '卖家A',
            last_item_id: 1, // 最后一条消息关联的商品ID
            last_time: '2025-10-28 10:30',
            last_sender: 'other', // 最后一条消息发送者（me/other）
            last_content: '这个商品还在吗？',
            unread_count: 1 // 未读消息数量
          },
          {
            other_user_id: 3,
            other_username: '买家B',
            last_item_id: 2,
            last_time: '2025-10-27 16:45',
            last_sender: 'me',
            last_content: '最低200元出，不议价',
            unread_count: 0
          }
        ];
      } finally {
        this.loading = false;
      }
    },

    // 格式化时间（简化版）
    formatTime(timeStr) {
      // 实际项目中可根据需要格式化（如：今天/昨天/具体日期）
      return timeStr;
    },

    // 进入与该用户的聊天界面
    goToChat(otherUserId, itemId) {
      this.$router.push({
        name: 'ChatDetail',
        params: {
          otherUserId: otherUserId,
          itemId: itemId
        }
      });
    }
  }
}
</script>

<style>
/* 头像样式 */
.avatar {
  font-weight: bold;
}

/* 消息列表项悬停效果 */
.list-group-item:hover {
  background-color: #f8f9fa;
}
</style>