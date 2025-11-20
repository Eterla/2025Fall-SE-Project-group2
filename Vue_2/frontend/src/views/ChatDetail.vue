<template>
  <div class="container mt-4">
    <!-- 聊天头部（显示对方信息和商品） -->
    <div class="card mb-3">
      <div class="card-body d-flex align-items-center gap-3">
        <button class="btn btn-outline-secondary" @click="$router.go(-1)">
          <i class="bi bi-arrow-left"></i>
        </button>

        <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
          {{ otherUserInfo.username?.charAt(0).toUpperCase() }}
        </div>
        <div>
          <h5 class="mb-0">{{ otherUserInfo.username }}</h5>
          <small class="text-muted">
            商品：<router-link :to="`/item/${itemId}`">{{ relatedItem.title || '未知商品' }}</router-link>
          </small>
        </div>
      </div>
    </div>

    <!-- 聊天消息区域 -->
    <div class="card mb-3" style="height: 500px; overflow-y: auto;" ref="scrollContainer" @scroll="onScroll">
      <div class="card-body p-4">
        <!-- 消息列表：按时间排序后一次性循环 -->
        <div class="d-flex flex-column gap-3">
          <template v-for="(msg, idx) in sortedMessages" :key="msg.id">
            <!-- 在第一条未读消息之前渲染未读分隔条 -->
            <div v-if="idx === firstUnreadIndex" class="text-center my-1">
              <span class="badge bg-info text-dark">最新消息</span>
            </div>

            <!-- 非我发出的消息 -->
            <div v-if="msg.from_user_id !== currentUserId" class="d-flex align-items-end gap-2">
              <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 30px; height: 30px; flex-shrink: 0;">
                {{ otherUserInfo.username?.charAt(0).toUpperCase() }}
              </div>
              <div>
                <div class="message-bubble message-bubble--other">
                  {{ msg.content }}
                </div>
                <small class="text-muted ms-2">{{ formatTime(msg.created_at) }}</small>
              </div>
            </div>

            <!-- 我发送的消息 -->
            <div v-else class="d-flex align-items-end justify-content-end gap-2">
              <div class="text-end">
                <div class="message-bubble message-bubble--me">
                  {{ msg.content }}
                </div>
                <small class="text-muted me-2">{{ formatTime(msg.created_at) }}</small>
              </div>
              <div class="avatar bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 30px; height: 30px; flex-shrink: 0;">
                {{ currentUserInfo.username?.charAt(0).toUpperCase() }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- “跳到最新”按钮（当不在底部且有未读/新消息时显示） -->
    <button v-if="showNewButton" class="btn btn-sm btn-info position-fixed" style="right:16px; bottom:86px; z-index:1000;" @click="jumpToLatest">
      新消息 {{ newCount > 0 ? '(' + newCount + ')' : '' }}
    </button>

    <!-- 消息输入区域 -->
    <div class="card">
      <div class="card-body p-3">
        <form @submit.prevent="sendMessage" class="d-flex gap-2">
          <textarea 
            class="form-control" 
            v-model="messageContent"
            @input="onInput" 
            @keydown="onKeydown"
            placeholder="输入消息..."
            rows="2"
            :disabled="sending"
          ></textarea>
          <button 
            type="submit" 
            class="btn btn-red" 
            :disabled="!messageContent.trim() || sending"
            style="white-space: nowrap;"
          >
            <span v-if="sending" class="spinner-border spinner-border-sm me-1"></span>
            发送
          </button>
        </form>
        <div v-if="typingNotice" class="mt-2 text-muted">{{ typingNotice }}</div>
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
      otherUserId: this.$route.params.otherUserId,
      itemId: this.$route.params.itemId,
      conversationId: this.$route.params.conversationId || null,
      messageContent: '',
      currentUserId: null,
      currentUserInfo: {},
      otherUserInfo: {},
      relatedItem: {},
      messageRefs: {},
      loading: true,
      sending: false,
      isScrolledUp: false, // 是否从底部向上滚动（用于显示“新消息”按钮）
      newlyArrived: 0 // 记录非活跃时到达的新消息数量
    }
  },
  computed: {
    chatStore() { return useChatStore() },
    messages() { return this.chatStore.getMessages(this.conversationId) || [] },
    sortedMessages() {
      return (this.messages || []).slice().sort((a, b) => {
        const ta = a && a.created_at ? new Date(a.created_at).getTime() : 0
        const tb = b && b.created_at ? new Date(b.created_at).getTime() : 0
        return ta - tb
      })
    },
    // 找到第一条未读（发给我的且 is_read === false）
    firstUnreadIndex() {
      const me = this.chatStore.getCurrentUserId()
      const arr = this.sortedMessages
      return arr.findIndex(m => m.to_user_id == me && !m.is_read)
    },
    typingNotice() {
      const t = (this.chatStore.typing && this.chatStore.typing[this.conversationId]) || {}
      const otherTyping = Object.keys(t || {}).find(uid => Number(uid) !== Number(this.currentUserId) && t[uid])
      return otherTyping ? '对方正在输入...' : ''
    },
    // 计算未读数（可用于显示角标）
    newCount() {
      // count messages that are to me and not read
      const me = this.chatStore.getCurrentUserId()
      return (this.messages || []).filter(m => m.to_user_id == me && !m.is_read).length
    },
    showNewButton() {
      // 当不在底部且有未读或刚到达的新消息时显示按钮
      return this.isScrolledUp && (this.newCount > 0 || this.newlyArrived > 0)
    }
  },
  created() {
    this.initUserInfo()
    this.getRelatedItem()

    const fallbackConv = `${Math.min(Number(this.currentUserId || 0), Number(this.otherUserId || 0))}_${this.itemId}`

    this.getHistoryMessages().then(() => {
      if (!this.conversationId) {
        this.conversationId = String(fallbackConv)
      }
      this.chatStore.setActiveSession(this.conversationId)
      const token = localStorage.getItem('access_token')
      socketService.connect(token)
      socketService.joinConversation(this.conversationId)
      socketService.onUserTyping(this._onUserTyping)

      // 监听 socket 的 new_message 并处理 UI 行为（计数/滚动）
      this._onNewMessage = (payload) => {
        // payload included conversation_id per API
        if (String(payload.conversation_id) !== String(this.conversationId)) return
        // add to store (SocketService may already do this; safe to call)
        this.chatStore.addMessage(payload)

        // 如果当前视图在底部（isScrolledUp === false），直接滚到底部并标为已读
        if (!this.isScrolledUp) {
          // 确保消息可见
          this.$nextTick(() => this.scrollToElement(null))
          // 标记为已读（并置 unreadCount=0）
          this.chatStore.markSessionRead(this.conversationId)
          // 可选：同步到后端标记已读（如后端支持），例如：
          // axios.post(`/messages/conversations/${this.conversationId}/read`).catch(()=>{})
        } else {
          // 用户不在底部，增加未查看的新消息计数（显示按钮）
          this.newlyArrived += 1
        }
      }
      socketService.onNewMessage(this._onNewMessage)
    })
  },
  beforeUnmount() {
    if (this.conversationId) {
      socketService.leaveConversation(this.conversationId)
    }
    socketService.offUserTyping(this._onUserTyping)
    socketService.offNewMessage(this._onNewMessage)
    const container = this.$refs.scrollContainer
    if (container && container.removeEventListener) container.removeEventListener('scroll', this.onScroll)
  },
  mounted() {
    // 如果 template 使用 ref scrollContainer，则 mounted 时可直接绑定滚动事件（防止事件绑定时容器还未存在）
    const container = this.$refs.scrollContainer
    if (container) {
      container.addEventListener('scroll', this.onScroll, { passive: true })
      // 初始化是否在底部
      this.onScroll()
    }
  },
  methods: {
    initUserInfo() {
      try {
        this.currentUserInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
        this.currentUserId = this.currentUserInfo.id
      } catch {
        this.currentUserInfo = {}
        this.currentUserId = null
      }
      this.otherUserInfo = { username: `用户${this.otherUserId}` }
    },

    async getRelatedItem() {
      try {
        const response = await axios.get(`/items/${this.itemId}`);
        if (response && response.ok) {
          this.relatedItem = response.data;
        }
      } catch (error) {
        this.relatedItem = { title: `商品${this.itemId}` }
      }
    },

    async getHistoryMessages() {
      try {
        const resp = await axios.get(`/messages/conversations/${this.otherUserId}/${this.itemId}`)
        const payload = resp && resp.data ? (resp.data.data ?? resp.data) : null
        if (Array.isArray(payload)) {
          const messages = payload
          if (messages.length > 0) {
            if (messages[0].conversation_id) {
              this.conversationId = String(messages[0].conversation_id)
            }
            messages.forEach(m => this.chatStore.addMessage(m))
          }
        }
      } catch (e) {
        console.error('getHistoryMessages error', e)
      } finally {
        this.loading = false
        this.$nextTick(() => this.scrollToFirstUnread())
      }
    },

    async onInput() {
      const me = this.chatStore.getCurrentUserId()
      socketService.sendTyping({
        user_id: Number(me),
        to_user_id: Number(this.otherUserId),
        item_id: Number(this.itemId),
        is_typing: !!this.messageContent && this.messageContent.trim().length > 0
      })
    },

    async _onUserTyping(data) {
      const conv = data && data.conversation_id ? String(data.conversation_id) : this.conversationId
      if (!conv) return
      this.chatStore.setTyping(conv, Number(data.user_id), !!data.is_typing)
    },

    // 当滚动时检测是否在底部
    onScroll() {
      const container = this.$refs.scrollContainer
      if (!container) return
      const threshold = 60 // 距底部多少 px 视为“在底部”
      const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight
      const wasScrolledUp = this.isScrolledUp
      this.isScrolledUp = distanceToBottom > threshold

      // 如果用户刚滚到底部（isScrolledUp 从 true -> false），把 newlyArrived 清零并标为已读
      if (wasScrolledUp && !this.isScrolledUp) {
        if (this.newlyArrived > 0) {
          // 将到达但未查看的消息标为已读
          this.chatStore.markSessionRead(this.conversationId)
          // 可向后端同步已读
          // axios.post(`/messages/conversations/${this.conversationId}/read`).catch(()=>{})
        }
        this.newlyArrived = 0
      }
    },

    onKeydown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (this.sending) return
        const content = (this.messageContent || '').trim()
        if (!content) return
        this.sendMessage()
      }
    },

    // 点击跳转到第一条未读或底部
    jumpToLatest() {
      const idx = this.firstUnreadIndex
      if (idx !== -1) {
        const msgs = this.sortedMessages
        const target = msgs[idx]
        const el = target && this.messageRefs[String(target.id)]
        if (el) {
          this.scrollToElement(el)
        } else {
          this.scrollToElement(null)
        }
      } else {
        this.scrollToElement(null)
      }
      // 进入后把未读置零
      this.chatStore.markSessionRead(this.conversationId)
      this.newlyArrived = 0
    },

    // 滚动操作（可传 element 或 null）
    scrollToElement(el) {
      if (el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        this.$nextTick(() => {
          const container = this.$el.querySelector('.card-body[style*="height: 500px"]')
          if (container) {
            container.scrollTop = container.scrollHeight
          }
        })
      }
    },

    scrollToFirstUnread() {
      const conv = this.conversationId
      if (!conv) {
        this.scrollToElement(null)
        return
      }
      const unread = this.newCount
      const msgs = this.sortedMessages || []
      if (unread > 0 && msgs.length > 0) {
        const idx = Math.max(0, msgs.length - unread)
        const target = msgs[idx]
        const el = target && this.messageRefs[String(target.id)]
        if (el) {
          this.scrollToElement(el)
          return
        }
      }
      this.scrollToElement(null)
    },

    setMessageRef(el, msgId) {
      if (el) {
        this.messageRefs[String(msgId)] = el
      } else {
        delete this.messageRefs[String(msgId)]
      }
    },

    async sendMessage() {
      const content = this.messageContent.trim()
      if (!content) return
      this.sending = true
      try {
        const resp = await axios.post('/messages', {
          to_user_id: this.otherUserId,
          item_id: this.itemId,
          content
        })
        if (resp && resp.ok) {
          if (resp.data && resp.data.conversation_id) {
            this.conversationId = String(resp.data.conversation_id)
            this.chatStore.setActiveSession(this.conversationId)
            socketService.joinConversation(this.conversationId)
          }
          this.chatStore.addMessage(resp.data)
          this.messageContent = ''
          this.$nextTick(() => this.scrollToElement(null))
        } else {
          alert((resp && resp.error && resp.error.message) || '发送失败')
        }
      } catch (e) {
        console.error('send failed', e)
      } finally {
        this.sending = false
      }
    },

    formatTime(timeStr) {
      return new Date(timeStr).toLocaleTimeString()
    }
  }
}
</script>

<style>
.max-width-50 { max-width: 50%; }
.card-body[style*="height: 500px"]::-webkit-scrollbar { width: 6px; }
.card-body[style*="height: 500px"]::-webkit-scrollbar-thumb { background-color: #ccc; border-radius: 3px; }

/* 消息气泡样式 */
.message-bubble {
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  display: inline-block;
  max-width: 40ch;  
  width: auto;
  white-space: normal; 
  overflow-wrap: break-word; 
  word-break: break-word;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  line-height: 1.35;
  font-size: 0.95rem;
}

/* 对方消息（左侧） */
.message-bubble--other {
  background: #f1f3f5;
  color: #212529;
  border-top-left-radius: 6px;
  border-top-right-radius: 12px;
  border-bottom-right-radius: 12px;
  border-bottom-left-radius: 12px;
}

/* 我发送的消息（右侧） */
.message-bubble--me {
  background: #900023;
  color: #fff;
  border-top-right-radius: 6px;
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  align-self: flex-end;
}

/* 时间戳样式 */
.msg-time {
  display: block;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  opacity: 0.8;
}
</style>