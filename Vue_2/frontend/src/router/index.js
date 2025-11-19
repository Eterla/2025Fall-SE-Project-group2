import { createRouter, createWebHistory } from 'vue-router';
// 导入你实际的页面组件（文件名与你的 views 文件夹一致）
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import ItemDetail from '../views/ItemDetail.vue';
import Publish from '../views/Publish.vue';
import UserCenter from '../views/UserCenter.vue';
import Favorites from '../views/Favorites.vue';
import Messages from '../views/Messages.vue';
import ChatDetail from '../views/ChatDetail.vue';
import Logout from '../views/Logout.vue';

// 保留登录守卫逻辑
const requireAuth = (to, from, next) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    next();
  } else {
    next('/login');
  }
};

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/login', name: 'Login', component: Login },
  { path: '/logout', name: 'Logout', component: Logout },
  { path: '/register', name: 'Register', component: Register },
  { path: '/item/:id', name: 'ItemDetail', component: ItemDetail },
  { path: '/publish', name: 'Publish', component: Publish, beforeEnter: requireAuth },
  { path: '/user-center', name: 'UserCenter', component: UserCenter, beforeEnter: requireAuth },
  { path: '/favorites', name: 'Favorites', component: Favorites, beforeEnter: requireAuth },
  { path: '/messages', name: 'Messages', component: Messages, beforeEnter: requireAuth },
  { path: '/conversations/:otherUserId/:itemId', name: 'ChatDetail', component: ChatDetail, beforeEnter: requireAuth }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;