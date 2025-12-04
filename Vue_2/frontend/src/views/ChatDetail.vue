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

    <!-- 聊天消息区域 -->
    <div class="card mb-3 chat-scroll-card" style="height: 500px; overflow-y: auto;" ref="scrollContainer" @scroll="onScroll">
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
// import { watch, ref } from 'vue' // 用来处理 DOM 更新后的操作


export default {
  data() {
    return {
      otherUserId: this.$route.params.otherUserId, // 路由里来的对方用户 id
      itemId: this.$route.params.itemId,           // 路由里来的商品 id
      conversationId: null, // 可能为空，等历史消息加载后确定

      messageContent: '',       // 输入框里的内容
      currentUserId: null,      // 从 localStorage 的 user_info 里解析
      currentUserInfo: {},      // 同上
      otherUserInfo: { username: null },        // 初始是 { username: 用户xxx }，之后可能被历史消息覆盖
      relatedItem: {},          // 商品标题等

      messageRefs: {},          // 想用来保存每条消息对应的 DOM 元素，但模板里现在没用上（稍后说）

      loading: true,            // 历史消息加载中
      sending: false,           // 是否正在发送消息

      isScrolledUp: false,      // 是否“离开底部”（用于控制“新消息”按钮）
      newlyArrived: 0           // 不在底部时，期间新到的消息数量
    }
  },
  computed: {
    chatStore() { return useChatStore() },
    messages() {
      // 所有原始消息
      const list = this.chatStore.getMessages(this.conversationId) || []

      // 按时间从旧到新排序
      const sorted = [...list].sort((a, b) => {
        const ta = new Date(a.created_at).getTime()
        const tb = new Date(b.created_at).getTime()
        return ta - tb
      })

      // 只展示最近的 N 条消息，避免每次从头开始刷
      const MAX_VISIBLE = 50
      if (sorted.length > MAX_VISIBLE) {
        return sorted.slice(sorted.length - MAX_VISIBLE)
      }
      return sorted
    },
    // 找第一个还没读的消息的索引
    firstUnreadIndex() {
      const me = this.chatStore.getCurrentUserId()
      const arr = this.messages
      return arr.findIndex(m => m.to_user_id == me && !m.is_read)
    },
    // 从chatStore里查看对方是否正在输入，使用userId定位
    typingNotice() {
      return this.chatStore.typing[this.otherUserId] || false
    },
    // 计算未读数
    newCount() {
      const me = this.chatStore.getCurrentUserId()
      const arr = this.messages
      console.log('计算 newCount', arr)
      const count = arr.filter(m => m.to_user_id == me && !m.is_read).length
      console.log('newCount=', count)
      return count
    },
    showNewButton() {
      // 当不在底部且有未读或刚到达的新消息时显示按钮
      return this.isScrolledUp && (this.newCount > 0 || this.newlyArrived > 0)
    }
  },
  // 页面加载到卸载所做的事情
  created() {
    // 拿当前用户信息（从localStorage）
    this.initUserInfo()
    // 拿商品信息(依赖 itemId)
    this.getRelatedItem()
    // 拿历史消息 （依赖 otherUserId 和 itemId）
    this.getHistoryMessages().then(() => {
      //将返回数组中的每条 message 写入 chatStore；如果消息带 conversation_id，就把组件的 conversationId 确定下来；
      
      // 告诉 store 当前活跃会话 setActiveSession(conversationId)；
      this.chatStore.setActiveSession(this.conversationId)
      // 用 token 建立 socket 连接
      const token = localStorage.getItem('access_token')
      socketService.connect(token)
      // 加入当前会话对应的房间；
      socketService.joinConversation(this.conversationId)

      // 注册两个监听函数：user_typing 和 new_message
      this._onUserTyping = this._onUserTyping.bind(this)
      socketService.onUserTyping(this._onUserTyping)
      this._onNewMessage = this._onNewMessage.bind(this)
      socketService.onNewMessage(this._onNewMessage)
    })
  },

  beforeUnmount() { // 清理 socket 事件和滚动事件
    if (this.conversationId) {
      socketService.leaveConversation(this.conversationId)
    }
    socketService.offUserTyping(this._onUserTyping)
    socketService.offNewMessage(this._onNewMessage)
    const container = this.$refs.scrollContainer
    if (container && container.removeEventListener) container.removeEventListener('scroll', this.onScroll)
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
              this.conversationId = String(messages[0].conversation_id) // 确定 conversationId  
            }
            if (Number(this.otherUserId) === Number(messages[0].from_user_id)) {
              this.otherUserInfo.username = messages[0].from_username
            } else {
              this.otherUserInfo.username = messages[0].to_username
            }
            // 将消息添加到 store
            messages.forEach(m => this.chatStore.addMessage(m))
          }
        }
      } catch (e) {
        console.error('getHistoryMessages error', e)
      } finally {
        this.loading = false
        // 获取完历史消息后滚动到第一条未读
        this.$nextTick(() => this.scrollToFirstUnread())
      }
    },
    // 输入事件 onInput 每次变化都会发送 typing 状态
    async onInput() {
      const me = this.chatStore.getCurrentUserId()
      console.log("发送 typing 事件")
      socketService.sendTyping({
        user_id: Number(me),
        to_user_id: Number(this.otherUserId),
        item_id: Number(this.itemId),
        is_typing: !!this.messageContent && this.messageContent.trim().length > 0
      })
      console.log("输入状态: ", !!this.messageContent && this.messageContent.trim().length > 0)
    },
    // 收到对方的 typing 事件 _onUserTyping
    async _onUserTyping(data) {
      console.log("收到 user_typing 数据:", data)
      this.chatStore.setTyping(data.user_id, data.item_id,!!data.is_typing)
    },

    async _onNewMessage(payload) {
      const msg = payload && payload.data ? payload.data : null
      if (!msg) return
      const convId = msg.conversation_id ? String(msg.conversation_id) : null
      if (convId !== this.conversationId) return

      // 1. 添加消息到 store
      this.chatStore.addMessage(msg)

      // 2. 根据是否在底部决定行为
      if (!this.isScrolledUp) {
        // 在底部：自动滚到最新
        this.$nextTick(() => this.scrollToElement(null))
      } else {
        // 离开底部：先不滚动，记一下“新消息数量”
        this.newlyArrived += 1
      }
    },

    // 当滚动时检测是否在底部
    onScroll() {
      const container = this.$refs.scrollContainer // 获取滚动容器
      if (!container) return
      const threshold = 5 // 距底部多少 px 视为“在底部”
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

          // 如果是首次发起会话，后端会返回 conversation_id，这里需要更新本地会话状态
          if (msg.conversation_id && !this.conversationId) {
            this.conversationId = String(msg.conversation_id)
            // 将当前会话设为活跃，并加入房间，保证后续 socket 推送正常
            this.chatStore.setActiveSession(this.conversationId)
            socketService.joinConversation(this.conversationId)
          }

          // typing 状态设为 false
          socketService.sendTyping({
            user_id: Number(this.currentUserId),
            to_user_id: Number(this.otherUserId),
            item_id: Number(this.itemId),
            is_typing: false
          })

          // 写入 store
          this.chatStore.addMessage(msg)

          // 清空输入并自动滚到底部（无论当前是否滚动到上方，都像 Messenger 一样跳到底）
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

/* 让聊天卡片作为浮动输入指示器的定位容器 */
.chat-scroll-card {
  position: relative;
}

/* 输入状态：浮动显示（当用户滚到上方时） */
.typing-indicator-floating {
  position: absolute;
  left: 50%;
  bottom: 8px; /* 紧贴聊天窗口底部中间 */
  transform: translateX(-50%);
  z-index: 900;
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