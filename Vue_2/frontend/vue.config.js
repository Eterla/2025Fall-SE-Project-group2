module.exports = {
  devServer: {
    port: 8080, // 前端开发服务器端口
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''
        },
        onProxyReq: (proxyReq, req, res) => {
          console.log(`代理请求: ${req.method} ${req.url} -> ${proxyReq.method} ${proxyReq.path}`);
        },
        onProxyRes: (proxyRes, req, res) => {
          console.log(`代理响应: ${req.method} ${req.url} <- ${proxyRes.statusCode} ${proxyRes.statusMessage}`);
        }
      }
    }
  }
}
