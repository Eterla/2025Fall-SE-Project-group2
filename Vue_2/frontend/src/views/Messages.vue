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
        @click="goToChat(conv.other_user_id, conv.item_id)"
      >
        <!-- 对方头像（用用户名首字母） -->
        <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px; flex-shrink: 0;">
          {{ conv.other_username.charAt(0).toUpperCase() }}
        </div>

        <!-- 消息内容 -->
        <div class="flex-grow-1 min-w-0">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <h6 class="mb-0">{{ conv.other_username }}</h6>
            <small class="text-muted">{{ formatTime(conv.last_message_time) }}</small>
          </div>
          <p class="mb-0 text-truncate">
            {{ conv.last_message_content }}
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
import socketService from '@/services/SocketService'
import { useChatStore } from '@/stores/chat'


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
    // socketService.connect(/);
    this._onNewMessage = (message) => {
      console.log('Messages.vue received new message:', message);
      this.getConversations(); // 收到新消息时刷新会话列表
    };
    socketService.on('new_message', this._onNewMessage);
  },
  methods: {
    // 获取消息会话列表
    async getConversations() {
      const chatStore = useChatStore()
      console.log("Messages.vue fetching conversations, current chatStore.sessions:", chatStore.sessions)
      try {
        // 调用后端接口获取消息列表
        const response = await axios.get('/messages/conversations');
        console.log('Messages/getConversations:', response);
        if (response.ok) {
          const data = response.data;
          this.conversations = data;
          // 更新 Pinia store 中的会话数据
          const mapped = data.map(conv => {
            return {
              id: conv.conversation_id,
              other_user_id: conv.other_user_id, 
              other_username: conv.other_username,
              item_id: conv.item_id,
              last_message_time: conv.last_message_time,
              last_message_content: conv.last_message_content,
              unreadCount: conv.unread_count
            }
          })
          chatStore.sessions = mapped
        } else {
          alert(response.error || '获取消息列表失败');
        }
      } catch (error) {
        console.error('获取消息列表失败:', error);
      } finally {
        this.loading = false;
      }
    },

    // 格式化时间（简化版）
    formatTime(timeStr) {
      if (!timeStr) return ''
      // 兼容 "YYYY-MM-DD HH:MM:SS" 和 ISO
      let d = new Date(timeStr)
      if (isNaN(d)) {
        d = new Date(timeStr.replace(' ', 'T'))
        if (isNaN(d)) return timeStr
      }

      const now = new Date()
      const dateOnly = dt => new Date(dt.getFullYear(), dt.getMonth(), dt.getDate())
      const diffDays = Math.round((dateOnly(d) - dateOnly(now)) / (24 * 60 * 60 * 1000))
      const timePart = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

      if (diffDays === 0) return `今天 ${timePart}`
      if (diffDays === -1) return `昨天 ${timePart}`
      if (diffDays === 1) return `明天 ${timePart}`

      if (d.getFullYear() === now.getFullYear()) {
        return `${d.getMonth() + 1}月${d.getDate()}日 ${timePart}`
      }
      // 不同年份使用完整日期
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${d.getFullYear()}-${mm}-${dd} ${timePart}`
    },

    // 进入与该用户的聊天界面
    goToChat(otherUserId, itemId) {
      this.$router.push({
        name: 'ChatDetail',
        params: {
          otherUserId: otherUserId,
          itemId: itemId,
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