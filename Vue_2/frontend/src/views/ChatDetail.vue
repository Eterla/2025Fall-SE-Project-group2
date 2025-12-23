<template>
  <div class="container mt-4 chat-detail-root">
    <!-- 聊天头部（显示对方信息和商品） -->
    <div class="chat-header">
      <div class="card mb-3">
        <div class="card-body d-flex align-items-center gap-3">
          <!-- return to messages -->
          <button class="btn btn-outline-secondary" @click="$router.push('/messages')">
            <i class="bi bi-arrow-left-short"></i>
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
          <div class="card-body d-flex align-items-center gap-3">
              <div class="ms-auto d-flex align-items-center gap-2">
                <button
                  class="btn btn-success"
                  :disabled="dealProcessing || !canCompleteDeal"
                  @click="confirmCompleteDeal"
                >
                  <span v-if="dealProcessing" class="spinner-border spinner-border-sm me-1"></span>
                  交易成功
                </button>
              </div>
            </div>
        </div>
      </div>
    </div>

    <!-- 聊天消息区域：增加一个 wrapper，把可滚动区域和悬浮 typing 气泡分开 -->
    <div class="chat-messages">
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
                <!-- 时间分隔（每隔 1 分钟显示一次时间） -->
                <div v-if="shouldShowTimeSeparator(index)" class="time-separator text-center my-2">
                  <span class="time-separator-text">{{ formatTimeShort(msg.created_at) }}</span>
                </div>

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
                  </div>
                </div>

                <!-- 新消息分界线：当用户在上方滚动且有新消息到达时，在边界后显示 -->
                <div v-if="newMessageBoundaryId && String(msg.id) === String(newMessageBoundaryId)" class="unread-separator d-flex align-items-center my-2">
                  <span class="unread-separator-line flex-grow-1"></span>
                  <span class="unread-separator-text mx-2">新消息</span>
                  <span class="unread-separator-line flex-grow-1"></span>
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

        <!-- 当用户往上滚动离开底部，但对方仍在输入时，悬浮显示 typing 气泡 -->
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
    </div>

    <!-- “跳到最新”按钮（当不在底部且有未读/新消息时显示） -->
    <button v-if="showNewButton" class="btn btn-red btn-info position-fixed" style="right:16px; bottom:86px; z-index:1000;" @click="jumpToLatest">
      新消息 {{ newCount > 0 ? '(' + newCount + ')' : '' }}
    </button>

    <!-- 消息输入区域 -->
    <div class="chat-input">
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
              ref="messageInput"
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
      newlyArrived: 0,
      newMessageBoundaryId: null,
      readTimer: null,
      dealProcessing: false
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
    },
    canCompleteDeal() {
      // 你后端字段可能叫 status / item_status；按你的 relatedItem 来
      const s = this.relatedItem?.status || this.relatedItem?.item_status
      // 未拉到商品信息时先允许点击也可以；这里选择更稳：必须 available 才能完成
      return !s || s === 'available'
    }
  },
  created() {
    this.initUserInfo()
    this.getRelatedItem()
    this.getHistoryMessages().then(async () => {
      this.chatStore.setActiveSession(this.conversationId)
      this.chatStore.markSessionRead(this.conversationId)
      await this.markConversationRead()
    
      socketService.joinConversation(this.conversationId)

      this._onUserTyping = this._onUserTyping.bind(this)
      socketService.onUserTyping(this._onUserTyping)
      this._onNewMessage = this._onNewMessage.bind(this)
      socketService.onNewMessage(this._onNewMessage)
    })
  },

  beforeUnmount() {
    // Mark session read and notify backend before leaving the chat view so the
    // Messages list reflects accurate unread counts.
    try {
      if (this.conversationId) {
        // locally mark read
        this.chatStore.markSessionRead(this.conversationId)
        // notify backend that messages were read
        this.markConversationRead().catch(err => console.warn('markConversationRead failed on beforeUnmount', err))
        // leave socket room
        socketService.leaveConversation(this.conversationId)
        // clear active session in store
        this.chatStore.setActiveSession(null)
      }
    } catch (e) {
      console.warn('beforeUnmount cleanup error', e)
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
            // Important: set active session and mark as read BEFORE adding history
            // so history messages won't be treated as new/unread by addMessage
            this.chatStore.setActiveSession(this.conversationId)
            this.chatStore.markSessionRead(this.conversationId)
            messages.forEach(m => this.chatStore.addMessage(m))
          }
        }
      } catch (e) {
        console.error('getHistoryMessages error', e)
      } finally {
        this.loading = false
        this.$nextTick(() => {
          this.scrollToFirstUnread()
          this.focusMessageInput()
        })
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
      const msg = (payload && payload.data) ? payload.data : payload || null
      if (!msg) return
      const convId = msg.conversation_id ? String(msg.conversation_id) : null
      if (convId !== this.conversationId) return

      const me = Number(this.chatStore.getCurrentUserId())

      // 先加到 store
      this.chatStore.addMessage(msg)

      // 如果用户在底部，并且这条消息是发给我的，则立刻“读掉”
      if (!this.isScrolledUp && Number(msg.to_user_id) === me && document.visibilityState === 'visible') {
        this.scheduleMarkRead()
      }

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
          this.markConversationRead()
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
      console.log('[ChatDetail] jumpToLatest called')
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
      this.markConversationRead()
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

          socketService.sendTyping({
            user_id: Number(this.currentUserId),
            to_user_id: Number(this.otherUserId),
            item_id: Number(this.itemId),
            is_typing: false
          })

          this.chatStore.addMessage(msg)
          this.chatStore.markSessionRead(this.conversationId)
          this.messageContent = ''
          this.isScrolledUp = false
          this.newlyArrived = 0
          // user sent a message -> clear the new-message boundary
          this.newMessageBoundaryId = null
          this.$nextTick(() => {
            this.scrollToElement(null)
            this.focusMessageInput()
          })
        } else {
          alert((resp && resp.error && resp.error.message) || '发送失败')
        }
      } catch (e) {
        console.error('send failed', e)
      } finally {
        this.sending = false
      }
    },

    focusMessageInput() {
      const input = this.$refs.messageInput
      if (input && typeof input.focus === 'function') {
        input.focus()
      }
    },

    // 显示时间分隔的判断：第一条或与上一条消息时间间隔 >= 60s
    shouldShowTimeSeparator(index) {
      const msgs = this.messages
      if (!msgs || msgs.length === 0) return false
      if (index === 0) return true
      const cur = new Date(msgs[index].created_at).getTime()
      const prev = new Date(msgs[index - 1].created_at).getTime()
      return (cur - prev) >= 60 * 1000 // 60 秒
    },

    // 格式化为 HH:MM（短时间）
    // 如果不是今天的消息，显示 MM月DD日 HH:MM
    // 如果不是同年份，显示 YYYY-MM-DD HH:MM
    formatTimeShort(timeStr) {
      const d = new Date(timeStr)
      const now = new Date()
      const isToday = d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
      const options = { hour: '2-digit', minute: '2-digit' }
      if (!isToday) {
        options.month = '2-digit'
        options.day = '2-digit'
      }
      if (d.getFullYear() !== now.getFullYear()) {
        options.year = 'numeric'
      }
      // 自定义格式
      let formatted = ''
      if (options.year) {
        formatted += `${d.getFullYear()}年`
      }
      if (options.month) {
        formatted += `${String(d.getMonth() + 1).padStart(2, '0')}月`
      }
      if (options.day) {
        formatted += `${String(d.getDate()).padStart(2, '0')}日 `
      }
      formatted += d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      return formatted.trim()
    },

    async markConversationRead() {
      if (!this.conversationId) return
      try {
        const resp = await axios.post(
          `/messages/conversations/${this.conversationId}/read`,
          {
            other_user_id: Number(this.otherUserId),
            item_id: Number(this.itemId),
          }
        )

        if (resp && resp.ok) {
          // 前端本地也同步一下（避免 UI 延迟）
          this.chatStore.markSessionRead(this.conversationId)
        } else {
          console.warn('markConversationRead failed:', resp)
        }
      } catch (e) {
        // 401/404/508 都在这里走
        console.warn('markConversationRead error:', e)
      }
    },
    scheduleMarkRead() {
      if (this.readTimer) return
      this.readTimer = setTimeout(async () => {
        this.readTimer = null
        this.chatStore.markSessionRead(this.conversationId)
        await this.markConversationRead()
      }, 300) // 300ms 内合并多条新消息
    },
    async confirmCompleteDeal() {
      if (!this.conversationId) return
      await this.completeDeal()
    },

    async completeDeal() {
      if (this.dealProcessing) return
      this.dealProcessing = true
      try {
        // 这里的 URL 需要你按后端实际实现二选一
        // 方案 A：POST /items/{itemId}/complete
        const resp = await axios.patch(`/items/${this.itemId}/status`, {
          ok: true,
          data: {
            id: Number(this.itemId),
            status: 'sold'
          }
        })

        if (resp && resp.ok) {
          // 让 ChatDetail 自己也变成“已完成”状态（可选）
          // 根据后端返回调整字段名
          const newStatus = resp.data.item_status
          this.relatedItem = { ...this.relatedItem, status: newStatus }

          // 关键：刷新会话列表，让 Messages 立刻变灰、Navbar 未读数也同步
          await this.refreshConversationsInStore()

          // 可选：回到消息列表
          this.$router.push('/messages')
        } else {
          alert((resp && resp.error) || '操作失败')
        }
      } catch (e) {
        console.warn('completeDeal failed', e)
        alert('操作失败（网络或服务器错误）')
      } finally {
        this.dealProcessing = false
      }
    },

    async refreshConversationsInStore() {
      // 统一走一次 conversations 刷新，保证 Messages / Navbar 都一致
      const store = this.chatStore
      try {
        const res = await axios.get('/messages/conversations')
        if (res && res.ok) {
          const data = res.data || []
          store.sessions = data.map(conv => ({
            id: conv.conversation_id,
            other_user_id: conv.other_user_id,
            other_username: conv.other_username,
            item_id: conv.item_id,
            last_message_time: conv.last_message_time,
            last_message_content: conv.last_message_content,
            unread_count: conv.unread_count,
            item_status: conv.item_status, // 建议加上，未来你可能在别处也要用
          }))
        }
      } catch (e) {
        console.warn('refreshConversationsInStore failed', e)
      }
    }
  }
}
</script>

<style>
.chat-detail-root {
  position: fixed;
  top: 56px;          /* navbar 高度 */
  left: 0;
  right: 0;
  bottom: 0;

  display: flex;
  flex-direction: column;

  overflow: hidden;  /* 禁止自己滚动 */
}
.max-width-50 { max-width: 50%; }
/* wrapper：非滚动定位容器 */
.chat-scroll-wrapper {
  position: relative;
}

.card-body {
  padding: 10px;
}

.chat-header {
  flex-shrink: 0;
}

.chat-input {
  flex-shrink: 0;
}

/* 消息卡片（实际可滚动区域） */
.chat-scroll-card {
  /* 保持 overflow 在这个元素上 */
  overflow-y: auto;
}

/* 时间分隔样式 */
.time-separator {
  font-size: 0.8rem;
  color: #6c757d;
}
.time-separator-text {
  display: inline-block;
  background: rgba(0,0,0,0.04);
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 500;
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

/* 时间戳样式（已移除单条时间显示） */
.msg-time {
  display: none;
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
/* 现在这个元素在 wrapper（非滚动容器）里，所以不会随内容滚 */
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