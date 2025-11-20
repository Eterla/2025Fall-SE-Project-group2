module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        }
      },
      '/images': {
       target: 'http://127.0.0.1:5001', // 后端地址（保持和后端运行地址一致）
        changeOrigin: true, // 必须恢复！解决跨域源地址问题
        pathRewrite: { '^/images': '/static/images' }, // 路径重写（前端/images → 后端/static/images）
        ws: false, // 禁用WebSocket代理（图片请求用不到，避免额外冲突）
        secure: false, // 开发环境禁用HTTPS校验（如果后端没开HTTPS）
         onProxyRes: (proxyRes) => {
          proxyRes.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate';
          proxyRes.headers['Pragma'] = 'no-cache';
          proxyRes.headers['Expires'] = '0';
        }
      }
    }
  }
}
