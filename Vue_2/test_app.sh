#!/bin/bash

echo "=== 校内二手物品交易平台 - 启动脚本 ==="
echo ""

# 检查是否安装了必要的工具
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "错误：未找到 $1，请先安装"
        exit 1
    fi
}

check_dependency "python3"
check_dependency "pip3"
check_dependency "npm"

# 启动后端
start_backend() {
    echo "1. 启动后端服务器..."
    cd backend || exit 1
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "   创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    echo "   安装后端依赖..."
    pip3 install -r requirements.txt
    
    # 初始化数据库
    echo "   初始化数据库..."
    flask init-db
    
    # 启动服务器
    echo "   启动后端服务器（http://localhost:5000）..."
    python3 run.py &
    BACKEND_PID=$!
    
    # 等待服务器启动
    sleep 5
    
    # 返回上级目录
    cd ..
}

# 启动前端
start_frontend() {
    echo "2. 启动前端服务器..."
    cd frontend || exit 1
    
    # 安装依赖
    echo "   安装前端依赖..."
    npm install
    
    # 启动服务器
    echo "   启动前端服务器（http://localhost:8080）..."
    npm run serve &
    FRONTEND_PID=$!
    
    # 返回上级目录
    cd ..
}

# 主函数
main() {
    # 启动后端
    start_backend
    
    # 启动前端
    start_frontend
    
    # 显示信息
    echo ""
    echo "=== 服务器启动完成 ==="
    echo "后端API: http://localhost:5000/api"
    echo "前端应用: http://localhost:8080"
    echo ""
    echo "按 Ctrl+C 停止服务器"
    echo ""
    
    # 等待用户输入
    wait $BACKEND_PID $FRONTEND_PID
}

# 捕获Ctrl+C信号
trap 'echo "停止服务器..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' SIGINT

# 启动应用
main
