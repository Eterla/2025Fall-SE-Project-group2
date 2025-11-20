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
      <div 
        class="list-group-item list-group-item-action d-flex gap-3 p-3 cursor-pointer"
        v-for="conv in conversations" 
        :key="conv.conversationId ?? conv.id ?? `${conv.other_user_id}_${conv.item_id}`"
        @click="goToChat(conv.other_user_id ?? conv.otherUserId, conv.item_id ?? conv.itemId)"
      >
        <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width:50px;height:50px;">
          {{ (conv.other_username ?? conv.otherUsername ?? '用户').charAt(0).toUpperCase() }}
        </div>

        <div class="flex-grow-1 min-w-0">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <h6 class="mb-0">{{ conv.other_username ?? conv.otherUsername ?? ('用户' + (conv.other_user_id ?? conv.otherUserId)) }}</h6>
            <small class="text-muted">{{ formatTime(conv.last_message_time ?? conv.lastMessageTime) }}</small>
          </div>
          <p class="mb-0 text-truncate message-preview">
            {{ conv.last_message_content ?? conv.lastMessage ?? '' }}
          </p>
        </div>

        <span v-if="(conv.unreadCount ?? conv.unread_count ?? 0) > 0" class="badge bg-danger align-self-start">
          {{ conv.unreadCount ?? conv.unread_count ?? 0 }}
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
    }
  },
  computed: {
    chatStore() { return useChatStore() },
    // 直接使用 store.sessions，保证 UI 随 store 更新而更新
    conversations() {
      return this.chatStore.sessions
    }
  },
  created() {
    // 页面加载时获取消息列表
    this.getConversations();
    socketService.onNewMessage(this._onSocketNewMessage);
  },
  beforeUnmount() {
    socketService.offNewMessage(this._onSocketNewMessage);
  },
  methods: {
    // 获取消息会话列表
    async getConversations() {
      try {
        const response = await axios.get('/messages/conversations')
        console.log('获取消息列表响应 yuiinbee：', response)
        if (response && response.ok) {
          const rawList = Array.isArray(response.data) ? response.data : (response.data.data ?? response.data)
          const unread = 0
          if (Array.isArray(rawList)) {
            rawList.forEach(s => {
              const normalized = {
                conversationId: s.conversation_id ?? s.conversationId ?? s.id ?? null,
                id: s.id ?? s.conversation_id ?? null,
                other_user_id: s.other_user_id ?? s.otherUserId ?? null,
                other_username: s.other_username ?? '',
                item_id: s.item_id ?? null,
                last_message_content: s.last_message_content ?? '',
                last_message_time: s.last_message_time ?? null,
                unreadCount: unread
              }
              this.chatStore.upsertSession(normalized)
            })
          }
        } 
      } catch (err) {
        console.error('获取消息列表失败:', err)
      } finally {
        this.loading = false
      }
    },
    

    _onSocketNewMessage(payload) {
      // payload 应包含 conversation_id 与消息内容
      try {
        this.chatStore.addMessage(payload)
      } catch (e) {
        console.error('_onSocketNewMessage error', e)
      }
    },

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

/* 消息预览文本溢出处理 */
.message-preview {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #777d83;
  font-size: 14px;
}
</style>