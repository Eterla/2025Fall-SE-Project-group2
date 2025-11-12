<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header bg-primary text-white">
            <h3 class="text-center">发布商品</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handlePublish">
              <!-- 商品标题 -->
              <div class="mb-3">
                <label for="title" class="form-label">商品标题 <span class="text-danger">*</span></label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="title" 
                  v-model="form.title" 
                  required
                  placeholder="请输入商品标题（如：二手 textbooks）"
                  maxlength="100"
                >
              </div>

              <!-- 商品价格 -->
              <div class="mb-3">
                <label for="price" class="form-label">商品价格（元）<span class="text-danger">*</span></label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="price" 
                  v-model="form.price" 
                  required
                  min="0.01" 
                  step="0.01"
                  placeholder="请输入价格"
                >
              </div>

              <!-- 商品描述 -->
              <div class="mb-3">
                <label for="description" class="form-label">商品描述 <span class="text-danger">*</span></label>
                <textarea 
                  class="form-control" 
                  id="description" 
                  v-model="form.description" 
                  required
                  rows="5"
                  placeholder="请描述商品详情（新旧程度、使用情况等）"
                ></textarea>
              </div>

              <!-- 商品图片（可选） -->
              <div class="mb-3">
                <label for="image" class="form-label">商品图片（可选）</label>
                <input 
                  type="file" 
                  class="form-control" 
                  id="image" 
                  accept="image/*"
                  @change="handleImageUpload"
                >
                <!-- 预览选中的图片 -->
                <div v-if="imagePreview" class="mt-2">
                  <img :src="imagePreview" class="img-thumbnail" style="max-width: 200px;" alt="预览图">
                </div>
              </div>

              <!-- 提交按钮 -->
              <button 
                type="submit" 
                class="btn btn-primary w-100" 
                :disabled="submitting"
              >
                <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
                {{ submitting ? '发布中...' : '发布商品' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      // 表单数据
      form: {
        title: '',        // 商品标题
        price: '',        // 商品价格
        description: '',  // 商品描述
        image: null       // 图片文件（不直接绑定v-model，通过change事件处理）
      },
      imagePreview: '',  // 图片预览地址
      submitting: false  // 提交状态（防止重复提交）
    }
  },
  methods: {
    // 处理图片上传预览
    handleImageUpload(e) {
      const file = e.target.files[0];
      if (!file) {
        // default image
        this.form.image = '2025Fall-SE-Project-group2/Vue_2/frontend/public/images/defaultPicture.png';
        return;
      }
      // 限制图片大小（如不超过5MB）
      if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB');
        e.target.value = ''; // 清空选中的文件
        return;
      }

      // 预览图片
      const reader = new FileReader();
      reader.onload = (event) => {
        this.imagePreview = event.target.result;
      };
      reader.readAsDataURL(file);

      // 保存文件到表单数据
      this.form.image = file;
    },

    // 提交发布商品
    async handlePublish() {
      // 简单验证
      if (!this.form.title.trim()) {
        alert('请输入商品标题');
        return;
      }
      if (!this.form.price || this.form.price < 0.01) {
        alert('请输入有效的商品价格');
        return;
      }
      if (!this.form.description.trim()) {
        alert('请输入商品描述');
        return;
      }

      this.submitting = true; // 开始提交，禁用按钮

      try {
        // 创建FormData对象（用于上传文件）
        const formData = new FormData();
        formData.append('title', this.form.title);
        formData.append('price', this.form.price);
        formData.append('description', this.form.description);
        if (this.form.image) {
          formData.append('image', this.form.image); // 图片文件
        }

        const axios = this.$axios;
        // 调用后端发布商品接口（暂时模拟，后续替换为真实请求）
        const response = await axios.post('/api/items', formData, {
          headers: {
            'Content-Type': 'multipart/form-data' // 上传文件必须的头信息
          }
        });

        if (response.data.ok) {
          alert('商品发布成功！');
          this.$router.push('/'); // 发布成功后跳回首页
        } else {
          alert(response.data.message || '发布失败，请重试');
        }
      } catch (error) {
        console.error('发布商品失败:', error);
        alert('网络错误，请稍后再试');
      } finally {
        this.submitting = false; // 结束提交，启用按钮
      }
    }
  }
}
</script>