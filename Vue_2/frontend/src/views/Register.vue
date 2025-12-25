<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-red text-white">
            <h3 class="text-center">用户注册</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleRegister">
              <!-- 用户名 -->
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="username" 
                  v-model="username" 
                  required
                  placeholder="请输入用户名"
                >
              </div>

              <!-- 密码 -->
              <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="password" 
                  v-model="password" 
                  required
                  placeholder="请输入密码"
                >
              </div>

              <!-- 确认密码 -->
              <div class="mb-3">
                <label for="confirmPassword" class="form-label">确认密码</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="confirmPassword" 
                  v-model="confirmPassword" 
                  required
                  placeholder="请再次输入密码"
                >
                <!-- 密码不一致提示 -->
                <p class="text-danger mt-1" v-if="password !== confirmPassword && confirmPassword">
                  两次密码输入不一致
                </p>
              </div>

              <!-- 邮箱 -->
              <div class="mb-3">
                <label for="email" class="form-label">邮箱</label>
                <input 
                  type="email" 
                  class="form-control" 
                  id="email" 
                  v-model="email" 
                  placeholder="请输入邮箱 (格式: 北大学生邮箱)"
                  @blur="validateEmail"
                >
                <!-- 邮箱格式错误提示 -->
                <p class="text-danger mt-1" v-if="emailError">
                  {{ emailError }}
                </p>
              </div>

              <button type="submit" class="btn btn-red w-100" :disabled="!isFormValid">
                注册
              </button>
            </form>
            <p class="text-center mt-3">
              已有账号？<router-link to="/login">立即登录</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 导入axios（后面会用于调用后端注册接口）
import axios from '@/axios'

export default {
  data() {
    return {
      username: '',       // 用户名
      password: '',       // 密码
      confirmPassword: '',// 确认密码
      email: '',          // 邮箱
      emailError: ''      // 邮箱错误信息
    }
  },
  computed: {
    // 计算表单是否有效
    isFormValid() {
      return this.username && 
             this.password && 
             this.confirmPassword && 
             this.password === this.confirmPassword && 
             this.validateEmailFormat() && 
             !this.emailError;
    }
  },
  methods: {
    // 验证邮箱格式
    validateEmail() {
      if (!this.email) {
        this.emailError = '邮箱不能为空';
        return false;
      }
      
      if (!this.validateEmailFormat()) {
        this.emailError = '邮箱格式错误，必须为10位学号@stu.pku.edu.cn格式';
        return false;
      }
      
      this.emailError = '';
      return true;
    },
    
    // 验证邮箱格式的具体逻辑
    validateEmailFormat() {
      // 正则表达式：10个数字 + @stu.pku.edu.cn
      const emailPattern = /^\d{10}@stu\.pku\.edu\.cn$/;
      return emailPattern.test(this.email);
    },
    
    async handleRegister() {
      // 验证密码一致性
      if (this.password !== this.confirmPassword) {
        alert('两次密码不一致');
        return;
      }
      
      // 验证邮箱格式
      if (!this.validateEmail()) {
        alert('请检查邮箱格式');
        return;
      }

      try {
        // 调用后端注册接口
        const response = await axios.post('/auth/register', {
          username: this.username,
          password: this.password,
          email: this.email
        });

        if (response.ok || response.status === 200) {
          alert('注册成功，请登录');
          this.$router.push('/login'); // 跳转到登录页
        } else {
          console.error('注册失败:', response.data);
          alert(response.data.message || '注册失败');
        }
      } catch (error) {
        console.error('注册请求失败:', error);
        alert('网络错误，请稍后再试');
      }
    }
  }
}
</script>