// src/stores/chat.js
import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [], // [{ id: conversation_id, other_user_id, other_username, item_id, lastMessage, unreadCount }]
    messages: {}, // { conversation_id: [msg1, msg2, ...] } msg 包含 is_read 字段
    activeSessionId: null, // 当前打开的会话 (conversation_id)
    typing: {} // { conversation_id: { user_id: isTyping } }
  }),

  actions: {
    // 打开会话（打开聊天窗口）
    setActiveSession(conversationId) {
      this.activeSessionId = conversationId
      this.markSessionRead(conversationId)
    },

    // 清空 store（登出时调用）
    clearAll() {
      this.sessions = []
      this.messages = {}
      this.activeSessionId = null
      this.typing = {}
    },

    // 插入或更新一个会话条目（供列表页面或首次收到消息时使用）
    upsertSession(session) {
      const s = this.sessions.find(x => x.id === session.id)
      if (s) {
        Object.assign(s, session)
      } else {
        this.sessions.unshift(Object.assign({}, session))
      }
    },

    // 添加消息（SocketService 或页面发送/获取历史时调用）
    addMessage(raw) {
      // 期望 raw 包含 conversation_id, from_user_id, to_user_id, item_id, content, created_at, is_read(optional)
      const conversationId = raw.conversation_id
      if (!conversationId) return

      const msg = {
        id: raw.id ?? Date.now(),
        conversation_id: conversationId,
        from_user_id: raw.from_user_id,
        to_user_id: raw.to_user_id,
        item_id: raw.item_id,
        content: raw.content,
        created_at: raw.created_at ?? new Date().toISOString(),
        sender_name: raw.from_username ?? raw.sender_name ?? '',
        // 如果后端返回 is_read 优先使用；否则根据当前 activeSession 判断（如果正在看该会话则已读）
        is_read: typeof raw.is_read === 'boolean' ? raw.is_read : (this.activeSessionId === conversationId)
      }

      // 确保 messages 数组存在
      if (!this.messages[conversationId]) {
        this.messages[conversationId] = []
      }

      // 去重：如果已有相同 id 则替换
      const existIdx = this.messages[conversationId].findIndex(m => String(m.id) === String(msg.id))
      if (existIdx !== -1) {
        this.messages[conversationId].splice(existIdx, 1, msg)
      } else {
        this.messages[conversationId].push(msg)
      }

      // 更新或创建 session 的 lastMessage & unreadCount
      let session = this.sessions.find(s => s.id === conversationId)
      if (session) {
        session.lastMessage = msg.content
        // 如果当前不是正在聊天的会话 → 未读+1（且消息是发给我的并未被标记为已读）
        if (this.activeSessionId !== conversationId && msg.to_user_id == this.getCurrentUserId() && !msg.is_read) {
          session.unreadCount = (session.unreadCount || 0) + 1
        }
      } else {
        // 新会话入口，unshift 到列表
        this.sessions.unshift({
          id: conversationId,
          other_user_id: msg.from_user_id === Number(this.getCurrentUserId()) ? msg.to_user_id : msg.from_user_id,
          other_username: msg.sender_name || `用户${msg.from_user_id}`,
          item_id: msg.item_id,
          lastMessage: msg.content,
          unreadCount: (this.activeSessionId === conversationId || msg.is_read) ? 0 : ((msg.to_user_id == this.getCurrentUserId()) ? 1 : 0)
        })
      }
    },

    // 将会话标记已读（未读置零），并把 messages 标记为 is_read=true
    markSessionRead(conversationIdRaw) {
      if (!conversationIdRaw) return
      const conversationId = String(conversationIdRaw)
      // 标记 messages 中为已读
      if (this.messages && this.messages[conversationId]) {
        this.messages[conversationId] = this.messages[conversationId].map(m => {
          return Object.assign({}, m, { is_read: true })
        })
      }
      // 更新 sessions 中的 unreadCount
      const s = this.sessions.find(s =>
        (s.conversationId && String(s.conversationId) === conversationId) ||
        (s.id && String(s.id) === conversationId)
      )
      if (s) s.unreadCount = 0
      // 如果 activeSessionId 不一致，保证同步
      if (String(this.activeSessionId) !== conversationId) {
        this.activeSessionId = conversationId
      }
    },

    // helper: 当前登录用户 id（从 localStorage 或其它存储取）
    getCurrentUserId() {
      try {
        const u = JSON.parse(localStorage.getItem('user_info') || '{}')
        return u.id
      } catch {
        return null
      }
    },

    // typing 状态处理
    setTyping(conversationId, userId, isTyping) {
      if (!this.typing[conversationId]) this.typing[conversationId] = {}
      this.typing[conversationId][userId] = !!isTyping
    }
  },

  getters: {
    // 获取某个会话的消息（如果没有返回空数组）
    getMessages: (state) => {
      return (conversationId) => state.messages[conversationId] || []
    },
    // 会话总未读数
    totalUnread: (state) => {
      return state.sessions.reduce((sum, s) => sum + (s.unreadCount || 0), 0)
    }
  }
})