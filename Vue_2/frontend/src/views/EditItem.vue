<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <!-- 返回按钮 -->
        <div class="mb-4">
          <button class="btn btn-outline-secondary" @click="userCenter">
            ← 返回个人中心
          </button>
        </div>

        <!-- 加载中提示 -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">正在加载商品信息...</p>
        </div>

        <!-- 商品不存在提示 -->
        <div v-if="!loading && !item" class="text-center py-5">
          <h3>商品不存在或已被删除</h3>
          <router-link to="/user-center" class="btn btn-red mt-3">返回个人中心</router-link>
        </div>

        <!-- 编辑表单 -->
        <div v-if="!loading && item">
          <!-- 系统提示信息 -->
          <div v-if="systemMessage" 
               :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger']" 
               role="alert">
            {{ systemMessage }}
          </div>

          <div class="card">
            <div class="card-header bg-red text-white">
              <h3>编辑商品信息</h3>
            </div>
            <div class="card-body">
              <form @submit.prevent="updateItem">
                
                <!-- 商品图片 -->
                <div class="mb-4">
                  <h5>商品图片</h5>
                  <div class="row">
                    <!-- 当前图片预览 -->
                    <div class="col-md-4 mb-3">
                      <div class="card">
                        <div class="card-header bg-light">当前图片</div>
                        <div class="card-body p-0">
                          <img 
                            :src="item.imagePath ? '/' + item.imagePath.replace(/\\/g, '/') : require('@/assets/images/defaultPicture.png')"  
                            class="img-fluid rounded" 
                            style="height: 200px; object-fit: cover;"
                            :alt="item.title"
                          >
                        </div>
                      </div>
                    </div>
                    
                    <!-- 新图片上传 -->
                    <div class="col-md-8">
                      <div class="mb-3">
                        <label for="imageUpload" class="form-label">更换商品图片</label>
                        <input 
                          type="file" 
                          class="form-control" 
                          id="imageUpload" 
                          ref="imageInput"
                          accept="image/*"
                          @change="handleImageUpload"
                          :disabled="uploadingImage"
                        >
                        <div class="form-text">
                          支持 JPG、PNG 格式，建议尺寸 800×600 像素，大小不超过 5MB
                        </div>
                      </div>
                      
                      <!-- 新图片预览 -->
                      <div v-if="imagePreview" class="mt-3">
                        <label class="form-label">新图片预览</label>
                        <div class="position-relative d-inline-block">
                          <img 
                            :src="imagePreview" 
                            class="img-thumbnail" 
                            style="height: 150px; object-fit: cover;"
                            alt="新图片预览"
                          >
                          <button 
                            v-if="imagePreview"
                            class="btn btn-sm btn-danger position-absolute top-0 end-0 rounded-circle" 
                            style="width: 25px; height: 25px; padding: 0; font-size: 12px;"
                            @click="removeImage"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <hr>

                <!-- 商品标题 -->
                <div class="mb-3">
                  <label for="title" class="form-label">商品标题</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="title" 
                    v-model="item.title" 
                    required
                    placeholder="请输入商品标题"
                  >
                </div>

                <!-- 商品价格 -->
                <div class="mb-3">
                  <label for="price" class="form-label">商品价格</label>
                  <div class="input-group">
                    <span class="input-group-text">¥</span>
                    <input 
                      type="number" 
                      class="form-control" 
                      id="price" 
                      v-model.number="item.price" 
                      required
                      min="0"
                      step="0.01"
                      placeholder="请输入价格"
                    >
                  </div>
                </div>

                <!-- 商品描述 -->
                <div class="mb-3">
                  <label for="description" class="form-label">商品描述</label>
                  <textarea 
                    class="form-control" 
                    id="description" 
                    v-model="item.description" 
                    rows="4"
                    placeholder="请输入商品详细描述"
                  ></textarea>
                </div>

                <!-- 商品标签 -->
                <div class="mb-3">
                  <label for="tags" class="form-label">商品标签</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="tags" 
                    v-model="tagsString"
                    placeholder="请输入标签，用逗号、空格或分号分隔"
                  >
                  <div class="form-text">
                    例如：二手, 书籍, 电子产品
                  </div>
                  <!-- 标签预览 -->
                  <div v-if="parsedTags.length > 0" class="mt-2">
                    <div class="d-flex flex-wrap gap-1">
                      <span 
                        v-for="(tag, idx) in parsedTags" 
                        :key="idx" 
                        class="badge bg-secondary"
                      >
                        {{ tag }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 商品状态 -->
                <div class="mb-4">
                  <label for="status" class="form-label">商品状态</label>
                  <select 
                    class="form-select" 
                    id="status" 
                    v-model="item.status"
                    required
                  >
                    <option value="available">可交易</option>
                    <option value="sold">已售出</option>
                  </select>
                </div>

                <!-- 提交按钮 -->
                <div class="d-flex gap-2">
                  <button 
                    type="submit" 
                    class="btn btn-red flex-1"
                    :disabled="!isFormValid || updating"
                  >
                    {{ updating ? '更新中...' : '保存修改' }}
                  </button>
                  <button 
                    type="button" 
                    class="btn btn-outline-danger flex-1"
                    @click="deleteItem"
                    :disabled="deleting"
                  >
                    {{ deleting ? '删除中...' : '删除商品' }}
                  </button>
                </div>
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
import dayjs from '@/utils/dayjs-plugins.js'

export default {
  name: 'EditItem',
  data() {
    return {
      loading: true,
      updating: false,
      deleting: false,
      uploadingImage: false,
      uploadProgress: 0,
      
      // 商品信息
      item: null,
      
      // 图片上传相关
      imageFile: null,
      imagePreview: null,
      
      // 标签字符串（用于编辑）
      tagsString: '',
      
      // 系统消息
      systemMessage: '',
      messageType: 'success'
    }
  },
  computed: {
    // 解析标签字符串为数组
    parsedTags() {
      if (!this.tagsString) return []
      return this.tagsString
        .split(/[\s,;，]+/)
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0)
    },
    
    // 验证表单是否有效
    isFormValid() {
      return this.item && 
             this.item.title && 
             this.item.title.trim() !== '' && 
             this.item.price !== null && 
             this.item.price !== undefined && 
             this.item.price >= 0 && 
             this.item.status
    }
  },
  created() {
    this.loadItem()
  },
  methods: {
    // 加载商品信息
    async loadItem() {
      const itemId = this.$route.params.id
      try {
        this.loading = true
        
        const response = await axios.get(`/items/${itemId}`)
        console.log('商品详情响应:', response)
        
        if (!response.data) {
          throw new Error('商品不存在')
        }
        
        const respData = response.data
        
        // 格式化时间
        const rawTime = respData.createdAt || respData.created_at
        let formattedTime = '暂无时间'
        if (rawTime) {
          try {
            const dayjsObj = dayjs(rawTime)
            if (dayjsObj.isValid()) {
              formattedTime = dayjsObj.format('YYYY-MM-DD HH:mm:ss')
            } else {
              formattedTime = '时间格式无效'
            }
          } catch (error) {
            console.error('时间处理报错:', error)
            formattedTime = '时间解析失败'
          }
        }
        
        // 规范化商品数据
        this.item = {
          ...respData,
          imagePath: respData.image_path || '',
          createdAt: formattedTime,
          id: respData.id,
          seller_id: respData.seller_id,
          seller_name: respData.seller_name
        }
        
        // 处理标签
        if (respData.tags) {
          if (Array.isArray(respData.tags)) {
            this.tagsString = respData.tags.join(', ')
          } else if (typeof respData.tags === 'string') {
            this.tagsString = respData.tags
          }
        }
        
      } catch (error) {
        console.error('加载商品信息失败:', error)
        this.showMessage('加载商品信息失败，请刷新重试', 'danger')
        this.item = null
      } finally {
        this.loading = false
      }
    },
    
    // 返回个人中心
    userCenter() {
      this.$router.push('/user-center');
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
    
    // 处理图片上传
    handleImageUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        this.showMessage('请选择图片文件', 'danger')
        this.$refs.imageInput.value = ''
        return
      }
      
      // 验证文件大小（限制为5MB）
      if (file.size > 5 * 1024 * 1024) {
        this.showMessage('图片大小不能超过5MB', 'danger')
        this.$refs.imageInput.value = ''
        return
      }
      
      this.imageFile = file
      
      // 创建预览
      const reader = new FileReader()
      reader.onload = (e) => {
        this.imagePreview = e.target.result
      }
      reader.readAsDataURL(file)
    },
    
    // 移除图片预览
    removeImage() {
      this.imagePreview = null
      this.imageFile = null
      if (this.$refs.imageInput) {
        this.$refs.imageInput.value = ''
      }
    },
    
    // 更新商品信息
    async updateItem() {
      if (!this.isFormValid) {
        this.showMessage('请填写完整的商品信息', 'danger')
        return
      }
      
      try {
        this.updating = true
        
        // 创建FormData对象，支持文件上传
        const formData = new FormData()
        
        // 添加图片文件（如果有新图片）
        if (this.imageFile) {
          formData.append('image', this.imageFile)
        }
        
        // 添加商品信息
        formData.append('title', this.item.title)
        formData.append('price', this.item.price)
        formData.append('description', this.item.description || '')
        formData.append('status', this.item.status)
        
        // 添加标签
        if (this.parsedTags.length > 0) {
          formData.append('tags', this.parsedTags.join(','))
        }
        
        // 发送更新请求
        const response = await axios.put(`/items/${this.item.id}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.ok) {
          this.showMessage('商品信息更新成功', 'success')
          
          // 延迟返回个人中心
          setTimeout(() => {
            this.$router.push('/user-center')
          }, 10)
        } else {
          throw new Error(response.data.message || '更新失败')
        }
      } catch (error) {
        console.error('更新商品信息失败:', error)
        this.showMessage(error.message || '更新失败，请稍后重试', 'danger')
      } finally {
        this.updating = false
      }
    },
    
    // 删除商品
    async deleteItem() {
      if (!confirm('确定要删除这个商品吗？此操作不可撤销！')) {
        return
      }
      
      try {
        this.deleting = true
        
        const response = await axios.delete(`/items/${this.item.id}`)
        
        if (response.ok) {
          this.showMessage('商品删除成功', 'success')
          
          // 延迟返回个人中心
          setTimeout(() => {
            this.$router.push('/user-center')
          }, 10)
        } else {
          throw new Error(response.data.message || '删除失败')
        }
      } catch (error) {
        console.error('删除商品失败:', error)
        this.showMessage(error.message || '删除失败，请稍后重试', 'danger')
      } finally {
        this.deleting = false
      }
    }
  }
}
</script>

<style scoped>
/* 图片样式 */
.img-fluid {
  object-fit: cover;
}

/* 表单输入框样式 */
.form-control:focus,
.form-select:focus {
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

/* 标签徽章样式 */
.badge {
  font-size: 0.9em;
  padding: 0.4em 0.7em;
}

/* 文本区域样式 */
textarea {
  resize: vertical;
  min-height: 100px;
}
</style>