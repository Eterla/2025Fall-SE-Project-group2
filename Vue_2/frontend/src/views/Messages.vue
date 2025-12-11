<template>
  <div class="container">
    <!-- 加载中提示 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
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
        :class="{ 'conversation-muted': conv.item_status && conv.item_status !== 'available' }"
        v-for="conv in conversations" 
        :key="conv.other_user_id"
        @click="goToChat(conv.other_user_id, conv.item_id)"
      >
        <!-- 对方头像（用用户名首字母） -->
        <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px; flex-shrink: 0;">
          {{ conv.other_username.charAt(0).toUpperCase() }}
        </div>

        <!-- 消息内容 -->
        <div class="flex-grow-1 min-w-0 d-flex justify-content-between">
          <!-- 左侧：用户名 + 最后一条消息（紧凑排布） -->
          <div class="flex-grow-1 min-w-0">
            <h6 class="mb-0 text-truncate">
              {{ conv.other_username }} [{{ conv.item_title }}]
            </h6>
            <!-- 最后一条消息，紧贴用户名下面 -->
            <p class="mb-0 text-truncate" style="margin-top: 4px;">
              {{ conv.last_message_content }}
            </p>
          </div>

          <!-- 右侧：图片 + 时间 + Badge（全部预留固定空间） -->
          <div class="ms-3 d-flex align-items-center" style="min-width: 170px; justify-content: flex-end;">

            <!-- 图片固定占位：50px 宽 -->
            <div style="width: 50px; height: 50px;" class="me-2 flex-shrink-0">
              <img
                :src="conv.item_image"
                alt="item image"
                style="width: 100%; height: 100%; object-fit: cover;"
              >
            </div>

            <!-- 时间固定占位，比如预留一个最长可能的时间字符串宽度 -->
            <small
              class="text-muted me-2 text-end d-inline-block"
              style="width: 125px;" 
            >
              {{ formatTime(conv.last_message_time) }}
            </small>

            <!-- 未读 badge 固定占位 -->
            <div style="width: 28px; text-align: right;">
              <!-- 有未读显示 badge -->
              <span
                v-if="conv.unread_count > 0"
                class="badge bg-danger"
              >
                {{ conv.unread_count }}
              </span>

              <!-- 无未读保持占位，不跳动 -->
              <span
                v-else
                class="badge invisible"
              >
                0
              </span>
            </div>
          </div>
        </div>
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

/* 下架/不可用商品对应的会话样式（灰化但仍可点击） */
.conversation-muted {
  opacity: 0.55;
  filter: grayscale(40%);
}
.conversation-muted .badge {
  opacity: 0.9;
}
</style>