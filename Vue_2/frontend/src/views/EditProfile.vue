<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <!-- 返回按钮 -->
        <div class="mb-4">
          <button class="btn btn-outline-primary" @click="userCenter">
            ← 返回个人中心
          </button>
        </div>

        <!-- 加载中提示 -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">正在加载用户信息...</p>
        </div>

        <!-- 编辑表单 -->
        <div v-if="!loading">
          <!-- 系统提示信息 -->
          <div v-if="systemMessage" 
               :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger']" 
               role="alert">
            {{ systemMessage }}
          </div>

          <div class="card mb-4">
            <div class="card-header bg-red text-white">
              <h3>编辑个人资料</h3>
            </div>
            <div class="card-body">
              
              <!-- 头像上传部分 -->
              <div class="mb-5">
                <h4 class="mb-3">头像设置</h4>
                <div class="d-flex align-items-center">
                  <!-- 当前头像预览 -->
                  <div class="me-4">
                    <div class="position-relative">
                      <div class="avatar-preview bg-red text-white rounded-circle d-flex align-items-center justify-content-center" 
                           :style="{ 
                             width: '120px', 
                             height: '120px',
                             fontSize: '2.5rem',
                             backgroundImage: avatarPreview ? `url(${avatarPreview})` : (userInfo.avatar_url ? `url(/${userInfo.avatar_url.replace(/\\/g, '/')})` : ''),
                             backgroundSize: 'cover',
                             backgroundPosition: 'center'
                           }">
                        <span v-if="!avatarPreview && !userInfo.avatar">
                          {{ userInfo.username?.charAt(0).toUpperCase() || 'U' }}
                        </span>
                      </div>
                      <!-- 移除按钮（当有预览图片时显示） -->
                      <button v-if="avatarPreview" 
                              class="btn btn-sm btn-danger position-absolute top-0 end-0 rounded-circle" 
                              style="width: 30px; height: 30px; padding: 0;"
                              @click="removeAvatar">
                        ×
                      </button>
                    </div>
                  </div>
                  
                  <!-- 上传控件 -->
                  <div class="flex-grow-1">
                    <div class="mb-3">
                      <label for="avatarUpload" class="form-label">上传新头像</label>
                      <input 
                        type="file" 
                        class="form-control" 
                        id="avatarUpload" 
                        ref="avatarInput"
                        accept="image/*"
                        @change="handleAvatarUpload"
                        :disabled="uploadingAvatar"
                      >
                      <div class="form-text">
                        支持 JPG、PNG 格式，建议尺寸 200×200 像素，大小不超过 2MB
                      </div>
                    </div>
                    
                    <!-- 上传进度条 -->
                    <div v-if="uploadingAvatar" class="progress mb-3">
                      <div class="progress-bar progress-bar-striped progress-bar-animated" 
                           :style="{ width: uploadProgress + '%' }">
                        {{ uploadProgress }}%
                      </div>
                    </div>
                    
                    <!-- 上传按钮 -->
                    <button 
                      class="btn btn-primary" 
                      :disabled="!avatarFile || uploadingAvatar"
                      @click="uploadAvatar"
                    >
                      {{ uploadingAvatar ? '上传中...' : '保存头像' }}
                    </button>
                  </div>
                </div>
              </div>

              <hr class="my-4">

              <!-- 基本信息表单 -->
              <form @submit.prevent="updateBasicInfo">
                <h4 class="mb-3">基本信息</h4>
                
                <!-- 用户名 -->
                <div class="mb-3">
                  <label for="username" class="form-label">用户名</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="username" 
                    v-model="userInfo.username" 
                    required
                    placeholder="请输入用户名"
                  >
                  <div class="form-text">用户名是公开显示的，请使用文明、健康的用户名</div>
                </div>
                
                <!-- 邮箱 -->
                <div class="mb-4">
                  <label for="email" class="form-label">邮箱</label>
                  <input 
                    type="email" 
                    class="form-control" 
                    id="email" 
                    v-model="userInfo.email" 
                    required
                    placeholder="请输入邮箱"
                    @blur="validateEmail"
                  >
                  <div v-if="emailError" class="text-danger mt-1">
                    {{ emailError }}
                  </div>
                  <div class="form-text">邮箱格式必须为10位学号@stu.pku.edu.cn</div>
                </div>
                
                <!-- 保存按钮 -->
                <button 
                  type="submit" 
                  class="btn btn-red" 
                  :disabled="!isBasicInfoValid || updatingBasicInfo"
                >
                  {{ updatingBasicInfo ? '保存中...' : '保存基本信息' }}
                </button>
              </form>

              <hr class="my-4">

              <!-- 更改密码表单 -->
              <form @submit.prevent="updatePassword">
                <h4 class="mb-3">更改密码</h4>
                
                <!-- 当前密码 -->
                <div class="mb-3">
                  <label for="currentPassword" class="form-label">当前密码</label>
                  <input 
                    type="password" 
                    class="form-control" 
                    id="currentPassword" 
                    v-model="password.current" 
                    required
                    placeholder="请输入当前密码"
                  >
                </div>
                
                <!-- 新密码 -->
                <div class="mb-3">
                  <label for="newPassword" class="form-label">新密码</label>
                  <input 
                    type="password" 
                    class="form-control" 
                    id="newPassword" 
                    v-model="password.new" 
                    required
                    placeholder="请输入新密码"
                    @input="validatePassword"
                  >
                  <div v-if="passwordError" class="text-danger mt-1">
                    {{ passwordError }}
                  </div>
                </div>
                
                <!-- 确认新密码 -->
                <div class="mb-4">
                  <label for="confirmPassword" class="form-label">确认新密码</label>
                  <input 
                    type="password" 
                    class="form-control" 
                    id="confirmPassword" 
                    v-model="password.confirm" 
                    required
                    placeholder="请再次输入新密码"
                    @input="validatePassword"
                  >
                  <div v-if="passwordConfirmError" class="text-danger mt-1">
                    {{ passwordConfirmError }}
                  </div>
                </div>
                
                <!-- 保存按钮 -->
                <button 
                  type="submit" 
                  class="btn btn-red" 
                  :disabled="!isPasswordValid || updatingPassword"
                >
                  {{ updatingPassword ? '更新中...' : '更改密码' }}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '@/axios'

export default {
  name: 'EditProfile',
  data() {
    return {
      loading: true,
      updatingBasicInfo: false,
      updatingPassword: false,
      uploadingAvatar: false,
      uploadProgress: 0,
      
      // 用户信息
      userInfo: {
        id: '',
        username: '',
        email: '',
        avatar: '',
        createdAt: ''
      },
      
      // 头像上传相关
      avatarFile: null,
      avatarPreview: null,
      
      // 密码相关
      password: {
        current: '',
        new: '',
        confirm: ''
      },
      
      // 验证错误信息
      emailError: '',
      passwordError: '',
      passwordConfirmError: '',
      
      // 系统消息
      systemMessage: '',
      messageType: 'success'
    }
  },
  computed: {
    // 验证基本信息是否有效
    isBasicInfoValid() {
      return this.userInfo.username && 
             this.userInfo.email && 
             this.validateEmailFormat(this.userInfo.email) && 
             !this.emailError
    },
    
    // 验证密码是否有效
    isPasswordValid() {
      return this.password.current && 
             this.password.new && 
             this.password.confirm && 
             this.password.new === this.password.confirm && 
             !this.passwordError && 
             !this.passwordConfirmError
    }
  },
  created() {
    this.loadUserInfo()
  },
  methods: {
    // 加载用户信息
    async loadUserInfo() {
      try {
        this.loading = true
        
        // 尝试从本地存储获取
        const userInfoStr = localStorage.getItem('user_info')
        if (userInfoStr) {
          this.userInfo = JSON.parse(userInfoStr)
        } else {
          // 如果没有，则从API获取
          const response = await axios.get('/auth/me')
          if (response.ok) {
            this.userInfo = response.data
          } else {
            throw new Error('无法获取用户信息')
          }
        }
        
        this.loading = false
      } catch (error) {
        console.error('加载用户信息失败:', error)
        this.showMessage('加载用户信息失败，请刷新重试', 'danger')
        this.loading = false
      }
    },
    
    // 显示消息
    showMessage(message, type = 'success') {
      this.systemMessage = message
      this.messageType = type
      
      // 3秒后自动清除消息
      setTimeout(() => {
        this.systemMessage = ''
      }, 3000)
    },

    userCenter() {
      this.$router.push('/user-center');
    },

    // 处理头像上传
    handleAvatarUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        this.showMessage('请选择图片文件', 'danger')
        this.$refs.avatarInput.value = ''
        return
      }
      
      // 验证文件大小（限制为2MB）
      if (file.size > 2 * 1024 * 1024) {
        this.showMessage('图片大小不能超过2MB', 'danger')
        this.$refs.avatarInput.value = ''
        return
      }
      
      this.avatarFile = file
      
      // 创建预览
      const reader = new FileReader()
      reader.onload = (e) => {
        this.avatarPreview = e.target.result
      }
      reader.readAsDataURL(file)
    },
    
    // 移除头像预览
    removeAvatar() {
      this.avatarPreview = null
      this.avatarFile = null
      this.$refs.avatarInput.value = ''
    },
    
    // 上传头像
    async uploadAvatar() {
      if (!this.avatarFile) return
      
      try {
        this.uploadingAvatar = true
        this.uploadProgress = 0
        
        // 创建FormData对象
        const formData = new FormData()
        formData.append('avatar', this.avatarFile)
        
        // 模拟上传进度（实际项目中根据实际情况调整）
        const interval = setInterval(() => {
          if (this.uploadProgress < 90) {
            this.uploadProgress += 10
          }
        }, 200)
        
        // 发送上传请求
        const response = await axios.post('/auth/upload-avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            // 实际的上传进度
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            this.uploadProgress = percentCompleted
          }
        })
        
        clearInterval(interval)
        this.uploadProgress = 100
        
        if (response.ok) {
          // 更新用户信息
          this.userInfo.avatar = response.data.avatarUrl
          
          // 更新本地存储
          localStorage.setItem('user_info', JSON.stringify(this.userInfo))
          
          this.showMessage('头像上传成功', 'success')
          
          // 重置上传状态
          setTimeout(() => {
            this.uploadingAvatar = false
            this.uploadProgress = 0
            this.avatarFile = null
            this.avatarPreview = null
            this.$refs.avatarInput.value = ''
          }, 500)
        } else {
          throw new Error(response.data.message || '上传失败')
        }
      } catch (error) {
        console.error('上传头像失败:', error)
        this.showMessage(error.message || '上传头像失败', 'danger')
        this.uploadingAvatar = false
        this.uploadProgress = 0
      }
    },
    
    // 验证邮箱格式
    validateEmail() {
      if (!this.userInfo.email) {
        this.emailError = '邮箱不能为空'
        return false
      }
      
      if (!this.validateEmailFormat(this.userInfo.email)) {
        this.emailError = '邮箱格式错误，必须为10位学号@stu.pku.edu.cn格式'
        return false
      }
      
      this.emailError = ''
      return true
    },
    
    // 邮箱格式验证逻辑
    validateEmailFormat(email) {
      const emailPattern = /^\d{10}@stu\.pku\.edu\.cn$/
      return emailPattern.test(email)
    },
    
    // 验证密码（只验证一致性，不验证格式）
    validatePassword() {
      // 清空之前的错误信息（移除了密码强度验证）
      this.passwordError = ''
      
      // 验证密码一致性
      if (this.password.confirm && this.password.new !== this.password.confirm) {
        this.passwordConfirmError = '两次输入的密码不一致'
      } else {
        this.passwordConfirmError = ''
      }
    },
    
    // 更新基本信息
    async updateBasicInfo() {
      if (!this.validateEmail()) {
        return
      }
      
      try {
        this.updatingBasicInfo = true
        
        const response = await axios.put('/auth/update-profile', {
          username: this.userInfo.username,
          email: this.userInfo.email
        })
        
        if (response.ok) {
          // 更新本地存储
          localStorage.setItem('user_info', JSON.stringify(this.userInfo))
          
          this.showMessage('基本信息更新成功', 'success')
        } else {
          throw new Error(response.data.message || '更新失败')
        }
      } catch (error) {
        console.error('更新基本信息失败:', error)
        this.showMessage(error.message || '更新失败，请稍后重试', 'danger')
      } finally {
        this.updatingBasicInfo = false
      }
    },
    
    // 更新密码
    async updatePassword() {
      this.validatePassword()
      
      if (!this.isPasswordValid) {
        return
      }
      
      try {
        this.updatingPassword = true
        
        const response = await axios.put('/auth/change-password', {
          currentPassword: this.password.current,
          newPassword: this.password.new
        })
        
        if (response.ok) {
          this.showMessage('密码修改成功', 'success')
          
          // 清空密码字段
          this.password = {
            current: '',
            new: '',
            confirm: ''
          }
          
          // 不移除登录状态，用户继续保持登录
        } else {
          throw new Error(response.data.message || '密码修改失败')
        }
      } catch (error) {
        console.error('修改密码失败:', error)
        this.showMessage(error.message || '密码修改失败，请检查当前密码', 'danger')
      } finally {
        this.updatingPassword = false
      }
    }
  }
}
</script>

<style scoped>
/* 头像预览样式 */
.avatar-preview {
  font-weight: bold;
  overflow: hidden;
}

/* 进度条动画 */
.progress-bar-animated {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% { background-position: 1rem 0; }
  100% { background-position: 0 0; }
}

/* 表单输入框样式 */
.form-control:focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 0.25rem rgba(220, 53, 69, 0.25);
}

/* 按钮样式 */
.btn-red {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
}

.btn-red:hover {
  background-color: #c82333;
  border-color: #bd2130;
}

.btn-red:disabled {
  background-color: #e35d6a;
  border-color: #e35d6a;
}

/* 返回按钮样式 */
.btn-outline-secondary:hover {
  background-color: #f8f9fa;
}
</style>