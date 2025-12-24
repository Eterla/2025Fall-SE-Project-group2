<template>
  <div class="container mt-4 mb-3">

    <!-- 加载状态：数据请求中显示 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- 空状态：无任何会话时显示 -->
    <div v-if="!loading && conversations.length === 0" class="text-center py-5">
      <p class="text-muted">你还没有任何消息</p>
      <router-link to="/" class="btn btn-red">去逛逛</router-link>
    </div>

    <!-- 会话列表 -->
    <div class="list-group" v-if="!loading && conversations.length > 0">

      <!-- 单个会话条目 -->
      <div
        v-for="conv in conversations"
        :key="`${conv.other_user_id}-${conv.item_id}`"
        class="list-group-item list-group-item-action d-flex gap-3 p-3 cursor-pointer"
        :class="{ 'conversation-muted': conv.item_status && conv.item_status !== 'available' }"
        @click="goToChat(conv.other_user_id, conv.item_id)"
      >

        <!-- 对方头像：使用用户名首字母 -->
        <div
          class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center"
          style="width: 50px; height: 50px; flex-shrink: 0;"
        >
          {{ conv.other_username.charAt(0).toUpperCase() }}
        </div>

        <!-- 会话主要内容区域 -->
        <div class="flex-grow-1 min-w-0 d-flex justify-content-between">

          <!-- 左侧：用户名 + 最后一条消息 -->
          <div class="flex-grow-1 min-w-0">
            <h6 class="mb-0 text-truncate">
              {{ conv.other_username }} [{{ conv.item_title }}]
            </h6>
            <p class="mb-0 text-truncate" style="margin-top: 4px;">
              {{ conv.last_message_content }}
            </p>
          </div>

          <!-- 右侧：商品图片 + 时间 + 未读数（固定布局，避免跳动） -->
          <div
            class="ms-3 d-flex align-items-center"
            style="min-width: 170px; justify-content: flex-end;"
          >

            <!-- 商品图片占位（固定 50x50） -->
            <div style="width: 50px; height: 50px;" class="me-2 flex-shrink-0">
              <img
                :src="conv.item_image
                  ? '/' + conv.item_image.replace(/\\/g, '/')
                  : require('@/assets/images/defaultPicture.png')"
                style="width: 100%; height: 100%; object-fit: cover;"
              >
            </div>

            <!-- 时间显示（预留固定宽度） -->
            <small
              class="text-muted me-2 text-end d-inline-block"
              style="width: 125px;"
            >
              {{ formatTime(conv.last_message_time) }}
            </small>

            <!-- 未读消息数（无未读时保留占位，防止布局抖动） -->
            <div style="width: 28px; text-align: right;">
              <span
                v-if="conv.unread_count > 0"
                class="badge bg-danger"
                :data-count="conv.unread_count > 99 ? '99plus' : ''"
              >
                {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
              </span>

              <span v-else class="badge invisible">0</span>
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
      loading: true,        // 是否处于加载状态
      conversations: []    // 会话列表数据
    }
  },

  created() {
    // 初始化时获取会话列表
    this.getConversations()

    // 监听 socket 新消息事件，用于实时刷新会话列表
    this._onNewMessage = (message) => {
      console.log('Messages.vue received new message:', message)
      this.getConversations()
    }

    socketService.on('new_message', this._onNewMessage)
  },

  beforeUnmount() {
    // 组件卸载时移除 socket 监听，防止内存泄漏
    if (this._onNewMessage) {
      socketService.off('new_message', this._onNewMessage)
    }
  },

  methods: {

    /**
     * 从后端获取会话列表，并同步更新 Pinia store
     */
    async getConversations() {
      const chatStore = useChatStore()
      console.log(
        'Messages.vue fetching conversations, current chatStore.sessions:',
        chatStore.sessions
      )

      try {
        const response = await axios.get('/messages/conversations')
        console.log('Messages/getConversations:', response)

        if (response.ok) {
          const data = response.data
          this.conversations = data

          // 映射为 Pinia 中使用的 session 结构
          chatStore.sessions = data.map(conv => ({
            id: conv.conversation_id,
            other_user_id: conv.other_user_id,
            other_username: conv.other_username,
            item_id: conv.item_id,
            last_message_time: conv.last_message_time,
            last_message_content: conv.last_message_content,
            unread_count: conv.unread_count
          }))
        } else {
          alert(response.error || '获取消息列表失败')
        }
      } catch (error) {
        console.error('获取消息列表失败:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * 将时间字符串格式化为更友好的显示形式
     */
    formatTime(timeStr) {
      if (!timeStr) return ''

      let d = new Date(timeStr)

      // 兼容非 ISO 格式时间
      if (isNaN(d)) {
        d = new Date(timeStr.replace(' ', 'T'))
        if (isNaN(d)) return timeStr
      }

      const now = new Date()
      const dateOnly = dt => new Date(dt.getFullYear(), dt.getMonth(), dt.getDate())
      const diffDays =
        Math.round((dateOnly(d) - dateOnly(now)) / (24 * 60 * 60 * 1000))

      const timePart = d.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      })

      if (diffDays === 0) return `今天 ${timePart}`
      if (diffDays === -1) return `昨天 ${timePart}`
      if (diffDays === 1) return `明天 ${timePart}`

      if (d.getFullYear() === now.getFullYear()) {
        return `${d.getMonth() + 1}月${d.getDate()}日 ${timePart}`
      }

      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${timePart}`
    },

    /**
     * 跳转到指定会话的聊天详情页
     */
    goToChat(otherUserId, itemId) {
      this.$router.push({
        name: 'ChatDetail',
        params: { otherUserId, itemId }
      })
    }
  }
}
</script>

<style>
/* 头像文字加粗 */
.avatar {
  font-weight: bold;
}

/* 会话悬停高亮 */
.list-group-item:hover {
  background-color: #f8f9fa;
}

/* 商品不可用时的会话弱化显示 */
.conversation-muted {
  opacity: 0.55;
  filter: grayscale(40%);
}

.conversation-muted .badge {
  opacity: 0.9;
}
</style>