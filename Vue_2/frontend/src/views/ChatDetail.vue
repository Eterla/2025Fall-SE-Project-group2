<template>
  <div class="container mt-4">
    <!-- 聊天头部（显示对方信息和商品） -->
    <div class="card mb-3">
      <div class="card-body d-flex align-items-center gap-3">
        <!-- 返回返回按钮 -->
        <button class="btn btn-outline-secondary" @click="$router.go(-1)">
          <i class="bi bi-arrow-left"></i>
        </button>
        
        <!-- 对方头像和名称 -->
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
    <div class="card mb-3" style="height: 500px; overflow-y: auto;">
      <div class="card-body p-4">
        <!-- 消息列表 -->
        <div class="d-flex flex-column gap-3">
          <!-- 对方发送的消息（循环过滤后的数组） -->
          <div class="d-flex align-items-end gap-2" v-for="msg in otherMessages" :key="msg.id">
            <div class="avatar bg-red text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 30px; height: 30px; flex-shrink: 0;">
              {{ otherUserInfo.username?.charAt(0).toUpperCase() }}
            </div>
            <div>
              <div class="bg-light p-2 rounded rounded-start-0 max-width-50">
                {{ msg.content }}
              </div>
              <small class="text-muted ms-2">{{ formatTime(msg.created_at) }}</small>
            </div>
          </div>

          <!-- 自己发送的消息（循环过滤后的数组） -->
          <div class="d-flex align-items-end justify-content-end gap-2" v-for="msg in myMessages" :key="msg.id">
            <div class="text-end">
              <div class="bg-red text-white p-2 rounded rounded-end-0 max-width-50">
                {{ msg.content }}
              </div>
              <small class="text-muted me-2">{{ formatTime(msg.created_at) }}</small>
            </div>
            <div class="avatar bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 30px; height: 30px; flex-shrink: 0;">
              {{ currentUserInfo.username?.charAt(0).toUpperCase() }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息输入区域 -->
    <div class="card">
      <div class="card-body p-3">
        <form @submit.prevent="sendMessage" class="d-flex gap-2">
          <textarea 
            class="form-control" 
            v-model="messageContent" 
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

export default {
  data() {
    return {
      // 路由参数
      otherUserId: this.$route.params.otherUserId, // 聊天对象ID
      itemId: this.$route.params.itemId,           // 关联商品ID

      // 数据
      messages: [],               // 消息列表（原始数据）
      messageContent: '',         // 输入的消息内容
      currentUserId: null,        // 当前登录用户ID
      currentUserInfo: {},        // 当前用户信息
      otherUserInfo: {},          // 聊天对象信息
      relatedItem: {},            // 关联商品信息

      // 状态
      loading: true,
      sending: false              // 发送中状态
    }
  },
  computed: {
    // 计算属性：过滤对方发送的消息
    otherMessages() {
      return this.messages.filter(msg => msg.sender_id !== this.currentUserId);
    },
    // 计算属性：过滤自己发送的消息
    myMessages() {
      return this.messages.filter(msg => msg.sender_id === this.currentUserId);
    }
  },
  created() {
    // 初始化数据
    this.initUserInfo();
    this.getRelatedItem();
    this.getHistoryMessages();

    // 模拟实时消息监听（实际项目中可用WebSocket）
    this.setupMessageListener();
  },
  methods: {
    // 初始化用户信息
    initUserInfo() {
      const userInfoStr = localStorage.getItem('user_info');
      if (userInfoStr) {
        this.currentUserInfo = JSON.parse(userInfoStr);
        this.currentUserId = this.currentUserInfo.id;
      }

      // 临时模拟聊天对象信息（实际应从接口获取）
      this.otherUserInfo = {
        username: `用户${this.otherUserId}` // 模拟用户名
      };
    },

    // 获取关联商品信息
    async getRelatedItem() {
      try {
        const response = await axios.get(`/items/${this.itemId}`);
        if (response.ok) {
          this.relatedItem = response.data;
        }
      } catch (error) {
        console.error('获取关联商品失败:', error);
        this.relatedItem = { title: `商品${this.itemId}` }; // 模拟商品名
      }
    },

    // 获取历史消息
    async getHistoryMessages() {
      try {
        const response = await axios.get(`/messages/history`, {
          params: {
            other_user_id: this.otherUserId,
            item_id: this.itemId
          }
        });
        if (response.ok) {
          this.messages = response.data;
        } else {
          alert('获取历史消息失败');
        }
      } catch (error) {
        console.error('获取历史消息失败:', error);
        // 模拟历史消息
        this.messages = [
          {
            id: 1,
            sender_id: this.otherUserId,
            content: '你好，这个商品还在吗？',
            created_at: '2025-10-28 10:30:00'
          },
          {
            id: 2,
            sender_id: this.currentUserId,
            content: '还在的，请问有兴趣吗？',
            created_at: '2025-10-28 10:35:00'
          }
        ];
      } finally {
        this.loading = false;
        this.scrollToBottom(); // 滚动到最新消息
      }
    },

    // 发送消息
    async sendMessage() {
      const content = this.messageContent.trim();
      if (!content) return;

      this.sending = true;
      try {
        // 调用后端发送消息接口
        const response = await axios.post('/messages/send', {
          other_user_id: this.otherUserId,
          item_id: this.itemId,
          content: content
        });

        if (response.ok) {
          // 发送成功，添加到消息列表
          this.messages.push(response.data);
          this.messageContent = ''; // 清空输入框
          this.scrollToBottom(); // 滚动到最新消息
        } else {
          alert(response.data.message || '发送失败');
        }
      } catch (error) {
        console.error('发送消息失败:', error);
        // 模拟发送成功（后端接口未实现时）
        this.messages.push({
          id: Date.now(), // 用时间戳作为临时ID
          sender_id: this.currentUserId,
          content: content,
          created_at: new Date().toLocaleString()
        });
        this.messageContent = '';
        this.scrollToBottom();
      } finally {
        this.sending = false;
      }
    },

    // 滚动到最新消息
    scrollToBottom() {
      const chatContainer = document.querySelector('.card-body[style*="height: 500px"]');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    },

    // 格式化时间
    formatTime(timeStr) {
      return new Date(timeStr).toLocaleTimeString(); // 显示时分秒
    },

    // 模拟实时消息监听（实际项目中用WebSocket）
    setupMessageListener() {
      // 仅做演示：5秒后模拟收到一条消息
      setTimeout(() => {
        if (this.messages.length > 0) {
          this.messages.push({
            id: Date.now() + 1,
            sender_id: this.otherUserId,
            content: '请问最低多少钱可以出？',
            created_at: new Date().toLocaleString()
          });
          this.scrollToBottom();
        }
      }, 5000);
    }
  }
}
</script>

<style>
/* 消息样式优化 */
.max-width-50 {
  max-width: 50%;
}

/* 滚动条美化 */
.card-body[style*="height: 500px"]::-webkit-scrollbar {
  width: 6px;
}
.card-body[style*="height: 500px"]::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 3px;
}
</style>