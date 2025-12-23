// src/stores/chat.js
import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],      // 会话列表
    messages: {},      // 每个会话的消息列表
    activeSessionId: null, // 当前打开的会话
    typing: {}         // 正在输入状态
  }),
  // sessions的格式：
  // [
  //  { id, 
  //    other_user_id, 
  //    other_username, 
  //    item_id, 
  //    lastMessage, 
  //    unread_count }
  // ]

  // messages 的格式：messages: { [conversationId]: Message[] }
  // Message 的格式：
  // {
  //   id,
  //   conversation_id,
  //   from_user_id,
  //   to_user_id,
  //   item_id,
  //   content,
  //   created_at,
  //   sender_name,
  //   is_read
  // }

  // typing: { [item_id]: {[userId]: boolean} } 

  actions: {
    // 打开会话（打开聊天窗口）
    setActiveSession(conversationId) {
      try {
        const convId = conversationId == null ? null : String(conversationId)
        console.log('setActiveSession:', convId)
        this.activeSessionId = convId
        // 当设置为 active 时，立即将其标为已读（本地）
        if (convId) this.markSessionRead(convId)
      } catch (e) {
        console.warn('setActiveSession error', e)
      }
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
      console.log("upsertSession:", session, "found existing:", s) // s 不存在时表示新会话
      if (s) {
        Object.assign(s, session) // 更新已有字段
      } else {
        console.log("upsertSession: adding new session", session)
        this.sessions.unshift(Object.assign({}, session)) // 新会话插入到最前面
      }

      // print
      console.log("当前 sessions 列表:", this.sessions)
    },

    // 添加消息（SocketService 或页面发送/获取历史时调用）
    addMessage(raw) {
      try {
        // normalize conversation id to string to avoid type mismatches
        const convIdRaw = raw.conversation_id
        if (!convIdRaw && convIdRaw !== 0) return
        const convId = String(convIdRaw)

        const msg = {
          id: raw.id,
          conversation_id: convId,
          from_user_id: raw.from_user_id,
          to_user_id: raw.to_user_id,
          item_id: raw.item_id,
          content: raw.content,
          created_at: raw.created_at,
          sender_name: raw.from_username ?? '',
          // treat message as read when this conversation is active
          is_read: !!raw.is_read || String(this.activeSessionId) === convId
        }

        // ensure messages array exists under string key
        if (!this.messages[convId]) {
          this.messages[convId] = []
        }

        // dedupe by id
        const existIdx = this.messages[convId].findIndex(m => String(m.id) === String(msg.id))
        if (existIdx !== -1) {
          this.messages[convId].splice(existIdx, 1, msg)
        } else {
          this.messages[convId].push(msg)
        }

        // update or create session
        let session = this.sessions.find(s => String(s.id) === convId)
        const currentUserId = this.getCurrentUserId()
        const shouldCountAsUnread = (msg.to_user_id == currentUserId) && !msg.is_read

        if (session) {
          session.lastMessage = msg.content
          // only increment unread when this conversation is NOT active
          if (String(this.activeSessionId) === convId) {
            // active session: ensure unread is zero
            session.unread_count = 0
          } else if (shouldCountAsUnread) {
            session.unread_count = (session.unread_count || 0) + 1
          }
        } else {
          // insert new session at front
          this.sessions.unshift({
            id: convId,
            other_user_id: msg.from_user_id === Number(currentUserId) ? msg.to_user_id : msg.from_user_id,
            other_username: msg.sender_name,
            item_id: msg.item_id,
            lastMessage: msg.content,
            unread_count: (String(this.activeSessionId) === convId || msg.is_read) ? 0 : (shouldCountAsUnread ? 1 : 0)
          })
        }
        // extra safety: if this conv is active, ensure its session unreadCount remains 0
        if (String(this.activeSessionId) === convId) {
          const s2 = this.sessions.find(s => String(s.id) === convId)
          if (s2) s2.unread_count = 0
        }
      } catch (e) {
        console.error('addMessage error:', e, 'raw message:', raw)
      }
    },

    // 将会话标记已读（未读置零），并把 messages 标记为 is_read=true
    markSessionRead(conversationId) {
      const convId = String(conversationId)
      let s = this.sessions.find(s => String(s.id) === convId)
      if (s) {
        console.log('markSessionRead for conversationId:', convId)
        s.unread_count = 0
      } else {
        this.upsertSession({ id: convId, unread_count: 0 })
      }

      const msgs = this.messages[convId]
      if (Array.isArray(msgs)) {
        const currentUserId = this.getCurrentUserId()
        for (const m of msgs) {
          // only mark messages sent to current user as read
          if (m.to_user_id == currentUserId) {
            m.is_read = true
          }
        }
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

    // 设置 typing 状态
    setTyping(userId, itemId, isTyping) {
      console.log("设置 typing 状态:", userId, itemId, isTyping)
      if (!this.typing[itemId]) {
        this.typing[itemId] = {}
      }
      this.typing[itemId][userId] = isTyping
    }
  },

  getters: {
    // 获取某个会话的消息（如果没有返回空数组）
    getMessages: (state) => {
      return (conversationId) => state.messages[conversationId] || []
    },
    // 会话总未读数
    totalUnread: (state) => {
      console.log("计算 chat.js 里 totalUnread")
      return state.sessions.reduce((sum, s) => sum + (s.unread_count || 0), 0)
    }
  }
})