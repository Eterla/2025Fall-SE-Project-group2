<template>
  <div class="container mt-4">
    <!-- 聊天头部（显示对方信息和商品） -->
    <div class="card mb-3">
      <div class="card-body d-flex align-items-center gap-3">
        <!-- return to messages -->
        <button class="btn btn-outline-secondary" @click="$router.push('/messages')">
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

    <!-- 聊天消息区域：增加一个 wrapper，把可滚动区域和悬浮 typing 气泡分开 -->
    <div class="chat-scroll-wrapper mb-3 position-relative">
      <div class="card chat-scroll-card" style="height: 500px; overflow-y: auto;" ref="scrollContainer" @scroll="onScroll">
        <div class="card-body p-4">
          <!-- 消息内容：展示给用户最新的消息 -->
          <div v-if="loading" class="text-center text-muted my-5">
            加载中...
          </div>
          <div v-else>
            <div 
              v-for="(msg, index) in messages" 
              :key="msg.id" 
              :ref="el => setMessageRef(el, msg.id)"
              :class="['flex-column', 'w-100']"
            >
              <!-- 未读分隔线：在第一条未读消息前插入 -->
              <div
                v-if="index === firstUnreadIndex"
                class="unread-separator d-flex align-items-center my-2"
              >
                <span class="unread-separator-line flex-grow-1"></span>
                <span class="unread-separator-text mx-2">以下为新消息</span>
                <span class="unread-separator-line flex-grow-1"></span>
              </div>

              <div
                :class="[
                  'd-flex',
                  msg.from_user_id === currentUserId ? 'justify-content-end' : 'justify-content-start',
                  'mb-3'
                ]"
              >
                <div :class="['message-bubble', msg.from_user_id === currentUserId ? 'message-bubble--me' : 'message-bubble--other']">
                  {{ msg.content }}
                  <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- 对方正在输入：在底部且接近最新时，内联显示 -->
            <div v-if="typingNotice && !isScrolledUp" class="typing-indicator-inline d-flex justify-content-start mb-2">
              <div class="message-bubble message-bubble--other typing-bubble">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 当用户往上滚动离开底部，但对方仍在输入时，悬浮显示 typing 气泡
           注意：这个元素现在是 chat-scroll-wrapper 的子元素（wrapper 非滚动容器），
           因此不会随消息内容滚动而被隐藏/移动 -->
      <div
        v-if="typingNotice && isScrolledUp"
        class="typing-indicator-floating"
      >
        <div class="message-bubble message-bubble--other typing-bubble">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>

    <!-- “跳到最新”按钮（当不在底部且有未读/新消息时显示） -->
    <!-- 不是碰到聊天窗口的时候才会显示，没碰到的时候收到新消息了就得显示 -->
    <button v-if="showNewButton" class="btn btn-red btn-info position-fixed" style="right:16px; bottom:86px; z-index:1000;" @click="jumpToLatest">
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
      conversationId: null,

      messageContent: '',
      currentUserId: null,
      currentUserInfo: {},
      otherUserInfo: { username: null },
      relatedItem: {},

      messageRefs: {},

      loading: true,
      sending: false,

      isScrolledUp: false,
      newlyArrived: 0
    }
  },
  computed: {
    chatStore() { return useChatStore() },
    messages() {
      const list = this.chatStore.getMessages(this.conversationId) || []
      const sorted = [...list].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      const MAX_VISIBLE = 50
      return sorted.length > MAX_VISIBLE ? sorted.slice(sorted.length - MAX_VISIBLE) : sorted
    },
    firstUnreadIndex() {
      const me = this.chatStore.getCurrentUserId()
      const arr = this.messages
      return arr.findIndex(m => m.to_user_id == me && !m.is_read)
    },
    typingNotice() {
      const typingObj = this.chatStore.typing || {}
      const itemTyping = typingObj[this.itemId] || {}
      return itemTyping[this.otherUserId] || false
    },
    newCount() {
      const me = this.chatStore.getCurrentUserId()
      const arr = this.messages
      const count = arr.filter(m => m.to_user_id == me && !m.is_read).length
      return count
    },
    showNewButton() {
      return this.isScrolledUp && (this.newCount > 0 || this.newlyArrived > 0)
    }
  },
  created() {
    this.initUserInfo()
    this.getRelatedItem()
    this.getHistoryMessages().then(() => {
      this.chatStore.setActiveSession(this.conversationId)
      const token = localStorage.getItem('access_token')
      socketService.connect(token)
      socketService.joinConversation(this.conversationId)

      this._onUserTyping = this._onUserTyping.bind(this)
      socketService.onUserTyping(this._onUserTyping)
      this._onNewMessage = this._onNewMessage.bind(this)
      socketService.onNewMessage(this._onNewMessage)
    })
  },

  beforeUnmount() {
    if (this.conversationId) {
      socketService.leaveConversation(this.conversationId)
    }
    socketService.offUserTyping(this._onUserTyping)
    socketService.offNewMessage(this._onNewMessage)
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
        const payload = resp && resp.data ? resp.data : null
        if (Array.isArray(payload)) {
          const messages = payload
          if (messages.length > 0) {
            if (messages[0].conversation_id) {
              this.conversationId = String(messages[0].conversation_id)
            }
            if (Number(this.otherUserId) === Number(messages[0].from_user_id)) {
              this.otherUserInfo.username = messages[0].from_username
            } else {
              this.otherUserInfo.username = messages[0].to_username
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
      this.chatStore.setTyping(data.user_id, data.item_id, !!data.is_typing)
    },

    async _onNewMessage(payload) {
      const msg = payload && payload.data ? payload.data : null
      if (!msg) return
      const convId = msg.conversation_id ? String(msg.conversation_id) : null
      if (convId !== this.conversationId) return

      this.chatStore.addMessage(msg)

      if (!this.isScrolledUp) {
        this.$nextTick(() => this.scrollToElement(null))
      } else {
        this.newlyArrived += 1
      }
    },

    onScroll() {
      const container = this.$refs.scrollContainer
      if (!container) return
      const threshold = 5
      const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight
      const wasScrolledUp = this.isScrolledUp
      this.isScrolledUp = distanceToBottom > threshold

      if (wasScrolledUp && !this.isScrolledUp) {
        if (this.newlyArrived > 0) {
          this.chatStore.markSessionRead(this.conversationId)
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

    jumpToLatest() {
      const idx = this.firstUnreadIndex
      if (idx !== -1) {
        const msgs = this.messages
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
      this.chatStore.markSessionRead(this.conversationId)
      this.newlyArrived = 0
    },

    scrollToElement(el) {
      if (el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        this.$nextTick(() => {
          const container = this.$refs.scrollContainer
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
      const msgs = this.messages
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
          const msg = resp.data || {}

          if (msg.conversation_id && !this.conversationId) {
            this.conversationId = String(msg.conversation_id)
            this.chatStore.setActiveSession(this.conversationId)
            socketService.joinConversation(this.conversationId)
          }
          this.chatStore.markSessionRead(this.conversationId)
          socketService.sendTyping({
            user_id: Number(this.currentUserId),
            to_user_id: Number(this.otherUserId),
            item_id: Number(this.itemId),
            is_typing: false
          })

          this.chatStore.addMessage(msg)

          this.messageContent = ''
          this.isScrolledUp = false
          this.newlyArrived = 0
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

/* wrapper：非滚动定位容器 */
.chat-scroll-wrapper {
  position: relative;
}

/* 消息卡片（实际可滚动区域） */
.chat-scroll-card {
  /* 保持 overflow 在这个元素上 */
  overflow-y: auto;
}

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

/* 未读分隔线 */
.unread-separator {
  font-size: 0.8rem;
  color: #868e96;
}
.unread-separator-line {
  height: 1px;
  background-color: #dee2e6;
}
.unread-separator-text {
  white-space: nowrap;
}

/* 输入状态：内联显示（在消息列表底部） */
.typing-indicator-inline {
  padding-left: 0.25rem;
}

/* 输入状态：浮动显示（当用户滚到上方时） */
/* 现在这个元素在 wrapper（非滚动容器）里，所以不会随内容滚动 */
.typing-indicator-floating {
  position: absolute;
  left: 50%;
  bottom: 12px; /* 靠近聊天窗口底部但不覆盖输入区域（如需调整请改这个值） */
  transform: translateX(-50%);
  z-index: 900;
  pointer-events: none; /* 不拦截点击事件 */
}

/* 三个跳动的点 */
.typing-bubble {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.typing-bubble .dot {
  display: inline-block;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: currentColor;
  margin: 0 2px;
  animation: typing-bounce 1s infinite ease-in-out;
  opacity: 0.6;
}

.typing-bubble .dot:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-bubble .dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing-bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>