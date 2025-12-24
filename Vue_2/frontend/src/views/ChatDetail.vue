<template>
  <div class="container mt-4 chat-detail-root">

    <!-- 顶部：聊天头部（返回 / 对方信息 / 商品信息 / 交易状态操作区） -->
    <div class="chat-header">
      <div class="card mb-3">
        <div class="card-body d-flex align-items-center gap-3">

          <!-- 返回消息列表 -->
          <button class="btn btn-outline-secondary" @click="$router.push('/messages')">
            <i class="bi bi-arrow-left-short"></i>
          </button>

          <!-- 对方头像：用户名首字母 -->
          <div
            class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center"
            style="width: 40px; height: 40px;"
          >
            {{ otherUserInfo.username?.charAt(0).toUpperCase() }}
          </div>

          <!-- 对方用户名 + 商品入口 -->
          <div class="min-w-0">
            <h5 class="mb-0 text-truncate">{{ otherUserInfo.username }}</h5>
            <small class="text-muted">
              商品：
              <router-link :to="`/item/${itemId}`">
                {{ relatedItem.title || '未知商品' }}
              </router-link>
            </small>
          </div>

          <!-- 右上角：交易状态区域（同一位置显示按钮/提示） -->
          <div class="ms-auto d-flex align-items-center gap-2">
            <!-- 卖家：显示“交易成功”按钮 -->
            <button
              v-if="isSeller"
              class="btn btn-success"
              :disabled="dealProcessing || !canCompleteDeal"
              @click="confirmCompleteDeal"
            >
              <span v-if="dealProcessing" class="spinner-border spinner-border-sm me-1"></span>
              交易成功
            </button>

            <!-- 买家：当交易已结束时显示提示 -->
            <span
              v-else-if="isDealClosed"
              class="badge bg-secondary"
              style="font-size: 0.9rem; padding: 0.5rem 0.75rem;"
            >
              该交易已结束
            </span>
          </div>

        </div>
      </div>
    </div>

    <!-- 中间：消息区（滚动容器 + 悬浮 typing 气泡） -->
    <div class="chat-messages">
      <div class="chat-scroll-wrapper mb-3 position-relative">

        <!-- 实际可滚动区域 -->
        <div
          class="card chat-scroll-card"
          style="height: 500px; overflow-y: auto;"
          ref="scrollContainer"
          @scroll="onScroll"
        >
          <div class="card-body p-4">

            <!-- 加载状态 -->
            <div v-if="loading" class="text-center text-muted my-5">
              加载中...
            </div>

            <!-- 消息列表 -->
            <div v-else>
              <div
                v-for="(msg, index) in messages"
                :key="msg.id"
                :ref="el => setMessageRef(el, msg.id)"
                :class="['flex-column', 'w-100']"
              >
                <!-- 时间分隔：第一条或与上一条间隔 >= 60s -->
                <div v-if="shouldShowTimeSeparator(index)" class="time-separator text-center my-2">
                  <span class="time-separator-text">{{ formatTimeShort(msg.created_at) }}</span>
                </div>

                <!-- 未读分隔：插在第一条未读消息之前 -->
                <div
                  v-if="index === firstUnreadIndex"
                  class="unread-separator d-flex align-items-center my-2"
                >
                  <span class="unread-separator-line flex-grow-1"></span>
                  <span class="unread-separator-text mx-2">以下为新消息</span>
                  <span class="unread-separator-line flex-grow-1"></span>
                </div>

                <!-- 单条消息气泡 -->
                <div
                  :class="[
                    'd-flex',
                    msg.from_user_id === currentUserId ? 'justify-content-end' : 'justify-content-start',
                    'mb-3'
                  ]"
                >
                  <div
                    :class="[
                      'message-bubble',
                      msg.from_user_id === currentUserId ? 'message-bubble--me' : 'message-bubble--other'
                    ]"
                  >
                    {{ msg.content }}
                  </div>
                </div>

                <!-- 新消息边界：用户在上方滚动时，用于标记“新消息”分界 -->
                <div
                  v-if="newMessageBoundaryId && String(msg.id) === String(newMessageBoundaryId)"
                  class="unread-separator d-flex align-items-center my-2"
                >
                  <span class="unread-separator-line flex-grow-1"></span>
                  <span class="unread-separator-text mx-2">新消息</span>
                  <span class="unread-separator-line flex-grow-1"></span>
                </div>
              </div>

              <!-- typing：当用户在底部（接近最新）时内联显示 -->
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

        <!-- typing：当用户滚动离开底部时，悬浮显示 -->
        <div v-if="typingNotice && isScrolledUp" class="typing-indicator-floating">
          <div class="message-bubble message-bubble--other typing-bubble">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>

      </div>
    </div>

    <!-- 跳到最新：当用户不在底部且存在未读/新到达消息时显示 -->
    <button
      v-if="showNewButton"
      class="btn btn-red btn-info position-fixed"
      style="right:16px; bottom:86px; z-index:1000;"
      @click="jumpToLatest"
    >
      新消息 {{ newCount > 0 ? '(' + newCount + ')' : '' }}
    </button>

    <!-- 底部：输入区 -->
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
      // 路由参数
      otherUserId: this.$route.params.otherUserId,
      itemId: this.$route.params.itemId,

      // 会话标识（由历史消息接口返回）
      conversationId: null,

      // 输入框内容
      messageContent: '',

      // 当前用户信息（从 localStorage 读取）
      currentUserId: null,
      currentUserInfo: {},

      // 对方信息（用户名来自历史消息接口）
      otherUserInfo: { username: null },

      // 商品信息
      relatedItem: {},

      // 消息 DOM 引用，用于定位滚动（msgId -> element）
      messageRefs: {},

      // 状态位
      loading: true,
      sending: false,

      // 滚动与未读相关状态
      isScrolledUp: false,
      newlyArrived: 0,
      newMessageBoundaryId: null,

      // 合并读回执（避免频繁请求）
      readTimer: null,

      // 交易按钮状态
      dealProcessing: false
    }
  },

  computed: {
    chatStore() { return useChatStore() },

    /**
     * 消息列表：从 store 取出后按时间排序，并限制最多显示最近 50 条
     */
    messages() {
      const list = this.chatStore.getMessages(this.conversationId) || []
      const sorted = [...list].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      const MAX_VISIBLE = 50
      return sorted.length > MAX_VISIBLE ? sorted.slice(sorted.length - MAX_VISIBLE) : sorted
    },

    /**
     * 第一条未读消息在 messages 中的索引（用于插入未读分隔）
     */
    firstUnreadIndex() {
      const me = this.chatStore.getCurrentUserId()
      const arr = this.messages
      return arr.findIndex(m => m.to_user_id == me && !m.is_read)
    },

    /**
     * 对方正在输入提示：按 itemId + otherUserId 取 typing 状态
     */
    typingNotice() {
      const typingObj = this.chatStore.typing || {}
      const itemTyping = typingObj[this.itemId] || {}
      return itemTyping[this.otherUserId] || false
    },

    /**
     * 当前视图中的未读条数（用于按钮显示）
     */
    newCount() {
      const me = this.chatStore.getCurrentUserId()
      return this.messages.filter(m => m.to_user_id == me && !m.is_read).length
    },

    /**
     * “跳到最新”按钮显示条件：用户滚离底部 + 存在未读/新到达
     */
    showNewButton() {
      return this.isScrolledUp && (this.newCount > 0 || this.newlyArrived > 0)
    },

    /**
     * 是否允许卖家完成交易：仅当商品处于 available 才可操作
     */
    canCompleteDeal() {
      const s = this.relatedItem?.status || this.relatedItem?.item_status
      return !s || s === 'available'
    },

    /**
     * 是否为卖家：用 currentUserId 与 relatedItem 的 seller_id 等字段比较
     */
    isSeller() {
      const me = Number(this.currentUserId)
      const sellerId = Number(this.relatedItem?.seller_id ?? this.relatedItem?.user_id ?? this.relatedItem?.owner_id)
      return !!me && !!sellerId && me === sellerId
    },

    /**
     * 交易是否已结束：只要状态不为 available 就视为结束
     */
    isDealClosed() {
      const s = this.relatedItem?.status || this.relatedItem?.item_status
      return !!s && s !== 'available'
    }
  },

  created() {
    // 初始化用户与商品信息
    this.initUserInfo()
    this.getRelatedItem()

    // 拉取历史消息后再建立 socket 监听，避免将历史当成“新消息”
    this.getHistoryMessages().then(async () => {
      this.chatStore.setActiveSession(this.conversationId)
      this.chatStore.markSessionRead(this.conversationId)
      await this.markConversationRead()

      socketService.joinConversation(this.conversationId)

      // 绑定并注册 socket 回调
      this._onUserTyping = this._onUserTyping.bind(this)
      socketService.onUserTyping(this._onUserTyping)

      this._onNewMessage = this._onNewMessage.bind(this)
      socketService.onNewMessage(this._onNewMessage)
    })
  },

  beforeUnmount() {
    // 页面离开前：本地标记已读 + 通知后端 + 离开 socket room + 清理监听
    try {
      if (this.conversationId) {
        this.chatStore.markSessionRead(this.conversationId)
        this.markConversationRead().catch(err => console.warn('markConversationRead failed on beforeUnmount', err))

        socketService.leaveConversation(this.conversationId)
        this.chatStore.setActiveSession(null)
      }
    } catch (e) {
      console.warn('beforeUnmount cleanup error', e)
    }

    socketService.offUserTyping(this._onUserTyping)
    socketService.offNewMessage(this._onNewMessage)
  },

  methods: {
    /**
     * 读取当前用户信息（localStorage: user_info）
     */
    initUserInfo() {
      try {
        this.currentUserInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
        this.currentUserId = this.currentUserInfo.id
      } catch {
        this.currentUserInfo = {}
        this.currentUserId = null
      }
    },

    /**
     * 获取商品信息：用于头部展示与交易状态判断
     */
    async getRelatedItem() {
      try {
        const response = await axios.get(`/items/${this.itemId}`)
        if (response && response.ok) {
          this.relatedItem = response.data
        }
      } catch (error) {
        this.relatedItem = { title: `商品${this.itemId}` }
      }
    },

    /**
     * 获取历史消息：
     * - 确定 conversationId
     * - 补齐 otherUserInfo.username
     * - 将历史写入 store（并在写入前先把 session 标记为已读）
     */
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

            // 关键：先 setActive + markRead，再 addMessage，避免历史被当成未读
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

    /**
     * 输入事件：发送 typing 状态给对方
     */
    async onInput() {
      const me = this.chatStore.getCurrentUserId()
      socketService.sendTyping({
        user_id: Number(me),
        to_user_id: Number(this.otherUserId),
        item_id: Number(this.itemId),
        is_typing: !!this.messageContent && this.messageContent.trim().length > 0
      })
    },

    /**
     * socket 回调：对方 typing 状态更新
     */
    async _onUserTyping(data) {
      this.chatStore.setTyping(data.user_id, data.item_id, !!data.is_typing)
    },

    /**
     * socket 回调：新消息到达
     * - 写入 store
     * - 若用户在底部且页面可见：合并触发读回执
     * - 若用户滚离底部：累计 newlyArrived
     */
    async _onNewMessage(payload) {
      const msg = (payload && payload.data) ? payload.data : payload || null
      if (!msg) return

      const convId = msg.conversation_id ? String(msg.conversation_id) : null
      if (convId !== this.conversationId) return

      const me = Number(this.chatStore.getCurrentUserId())

      this.chatStore.addMessage(msg)

      if (!this.isScrolledUp && Number(msg.to_user_id) === me && document.visibilityState === 'visible') {
        this.scheduleMarkRead()
      }

      if (!this.isScrolledUp) {
        this.$nextTick(() => this.scrollToElement(null))
      } else {
        this.newlyArrived += 1
      }
    },

    /**
     * 滚动事件：判断是否“离开底部”
     * - 回到底部时：清空 newlyArrived，并触发读回执（如有必要）
     */
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

    /**
     * 键盘：Enter 发送，Shift+Enter 换行
     */
    onKeydown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (this.sending) return
        const content = (this.messageContent || '').trim()
        if (!content) return
        this.sendMessage()
      }
    },

    /**
     * “跳到最新”：优先滚到第一条未读，否则滚到底部
     */
    jumpToLatest() {
      const idx = this.firstUnreadIndex

      if (idx !== -1) {
        const target = this.messages[idx]
        const el = target && this.messageRefs[String(target.id)]
        this.scrollToElement(el || null)
      } else {
        this.scrollToElement(null)
      }

      this.chatStore.markSessionRead(this.conversationId)
      this.newlyArrived = 0
      this.markConversationRead()
    },

    /**
     * 滚动定位：
     * - 有 element：滚到该元素
     * - 否则：滚到底部
     */
    scrollToElement(el) {
      if (el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        this.$nextTick(() => {
          const container = this.$refs.scrollContainer
          if (container) container.scrollTop = container.scrollHeight
        })
      }
    },

    /**
     * 初次进入：如果有未读，滚到第一条未读；否则滚到底部
     */
    scrollToFirstUnread() {
      const conv = this.conversationId
      if (!conv) return this.scrollToElement(null)

      const unread = this.newCount
      const msgs = this.messages

      if (unread > 0 && msgs.length > 0) {
        const idx = Math.max(0, msgs.length - unread)
        const target = msgs[idx]
        const el = target && this.messageRefs[String(target.id)]
        if (el) return this.scrollToElement(el)
      }

      this.scrollToElement(null)
    },

    /**
     * 记录每条消息对应的 DOM 引用，便于滚动定位
     */
    setMessageRef(el, msgId) {
      if (el) this.messageRefs[String(msgId)] = el
      else delete this.messageRefs[String(msgId)]
    },

    /**
     * 发送消息：
     * - 调后端创建消息
     * - 若是首次发送导致创建会话：补齐 conversationId 并 join room
     * - 发送完成后清空输入并滚动到底部
     */
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

    /**
     * 聚焦输入框：提升输入体验
     */
    focusMessageInput() {
      const input = this.$refs.messageInput
      if (input && typeof input.focus === 'function') input.focus()
    },

    /**
     * 时间分隔：第一条 or 与上一条间隔 >= 60 秒
     */
    shouldShowTimeSeparator(index) {
      const msgs = this.messages
      if (!msgs || msgs.length === 0) return false
      if (index === 0) return true

      const cur = new Date(msgs[index].created_at).getTime()
      const prev = new Date(msgs[index - 1].created_at).getTime()
      return (cur - prev) >= 60 * 1000
    },

    /**
     * 时间显示：今天仅显示 HH:MM；非今天显示 MM月DD日 HH:MM；跨年加上 YYYY
     */
    formatTimeShort(timeStr) {
      const d = new Date(timeStr)
      const now = new Date()

      const isToday =
        d.getFullYear() === now.getFullYear() &&
        d.getMonth() === now.getMonth() &&
        d.getDate() === now.getDate()

      let formatted = ''

      if (d.getFullYear() !== now.getFullYear()) {
        formatted += `${d.getFullYear()}年`
      }

      if (!isToday) {
        formatted += `${String(d.getMonth() + 1).padStart(2, '0')}月`
        formatted += `${String(d.getDate()).padStart(2, '0')}日 `
      }

      formatted += d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      return formatted.trim()
    },

    /**
     * 通知后端：将会话消息标记为已读，并同步前端 store
     */
    async markConversationRead() {
      if (!this.conversationId) return

      try {
        const resp = await axios.post(
          `/messages/conversations/${this.conversationId}/read`,
          {
            other_user_id: Number(this.otherUserId),
            item_id: Number(this.itemId)
          }
        )

        if (resp && resp.ok) {
          this.chatStore.markSessionRead(this.conversationId)
        } else {
          console.warn('markConversationRead failed:', resp)
        }
      } catch (e) {
        console.warn('markConversationRead error:', e)
      }
    },

    /**
     * 合并读回执：300ms 内多条新消息只触发一次 read 请求
     */
    scheduleMarkRead() {
      if (this.readTimer) return

      this.readTimer = setTimeout(async () => {
        this.readTimer = null
        this.chatStore.markSessionRead(this.conversationId)
        await this.markConversationRead()
      }, 300)
    },

    /**
     * 卖家点击“交易成功”前的入口（便于未来做确认弹窗）
     */
    async confirmCompleteDeal() {
      if (!this.conversationId) return
      await this.completeDeal()
    },

    /**
     * 完成交易：
     * - 调后端修改商品状态
     * - 刷新会话列表（让 Messages 视图立刻变灰）
     * - 可选：返回消息列表
     */
    async completeDeal() {
      if (this.dealProcessing) return
      this.dealProcessing = true

      try {
        const resp = await axios.patch(`/api/items/${this.itemId}/status`, {
          status: 'sold'
        })

        if (resp && resp.ok) {
          const newStatus = resp.data.item_status
          this.relatedItem = { ...this.relatedItem, status: newStatus }

          await this.refreshConversationsInStore()
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

    /**
     * 刷新会话列表到 store：用于 Messages 页面即时更新（灰化/未读数等）
     */
    async refreshConversationsInStore() {
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
            item_status: conv.item_status
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
/* 整页布局：固定在 navbar 下方，内部用 flex 管理头部/消息区/输入区 */
.chat-detail-root {
  position: fixed;
  top: 56px;   /* navbar 高度 */
  left: 0;
  right: 0;
  bottom: 0;

  display: flex;
  flex-direction: column;

  overflow: hidden; /* 禁止根容器滚动 */
}

/* 非滚动定位容器：用于悬浮 typing */
.chat-scroll-wrapper {
  position: relative;
}


/* 消息滚动区域 */
.chat-scroll-card {
  overflow-y: auto;
}

/* 时间分隔 */
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

/* 消息气泡通用样式 */
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

/* 对方消息 */
.message-bubble--other {
  background: #f1f3f5;
  color: #212529;
  border-top-left-radius: 6px;
}

/* 我发送的消息 */
.message-bubble--me {
  background: #900023;
  color: #fff;
  border-top-right-radius: 6px;
  align-self: flex-end;
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

/* typing：内联（底部） */
.typing-indicator-inline {
  padding-left: 0.25rem;
}

/* typing：悬浮（用户滚离底部） */
.typing-indicator-floating {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  z-index: 900;
  pointer-events: none;
}

/* typing 三点动画 */
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

.typing-bubble .dot:nth-child(2) { animation-delay: 0.15s; }
.typing-bubble .dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes typing-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-4px); opacity: 1; }
}
</style>