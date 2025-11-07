from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash  # 更安全的密码处理
from functools import wraps
import jwt
import datetime
from flask import current_app
# 在 auth.py 开头的导入部分添加
from .models import User  # 从当前目录的 models.py 中导入 User 类
from .exceptions import UsernameTakenError  # 从exceptions.py导入异常  <-- 修改这里
from flask import g  # 导入Flask的全局上下文对象g

auth_bp = Blueprint("auth", __name__)

# JWT 令牌生成
def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),  # 有效期24小时
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm='HS256'
    )

# 令牌验证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
        if not token:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "NO_TOKEN",
                    "message": "认证令牌缺失"
                }
            }), 401
            
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=['HS256']
            )
            current_user_id = payload['sub']
            session['user_id'] = current_user_id  # 兼容session逻辑
        except jwt.ExpiredSignatureError:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "令牌已过期"
                }
            }), 401
        except:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "无效的令牌"
                }
            }), 401
            
        return f(*args, **kwargs)
    
    return decorated

# 注册接口
@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    
    # 查看前端传来的数据
    print(f"注册请求数据：{data}")
    
    # 验证必填参数
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "用户名和密码不能为空"
            }
        }), 400
        
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    phone = data.get('phone', '')
    
    # 密码加密（自动加盐）
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    try:
        # 调用User模型创建用户（假设create方法返回新用户完整信息，含created_at）
        new_user = User.create(
            username=username,
            password=hashed_password,
            email=email,
            phone=phone
        )
        return jsonify({
            "ok": True,
            "data": {
                "id": new_user['id'],
                "username": new_user['username'],
                "email": new_user['email'],
                "phone": new_user['phone'],
                "created_at": new_user['created_at'].isoformat()
            }
        }), 201
    except UsernameTakenError:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USERNAME_TAKEN",
                "message": "用户名已被占用"
            }
        }), 409
    except Exception as e:
        # 捕获其他异常（如数据库错误）
        print(f"注册失败：{str(e)}")  # 仅后端打印，不暴露给前端
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "服务器内部错误"
            }
        }), 500

# 登录接口
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    
    # 验证必填参数
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "用户名和密码不能为空"
            }
        }), 400
        
    username = data.get('username')
    password = data.get('password')
    
    # 查询用户
    user = User.find_by_username(username)
    
    # 区分错误类型
    if not user:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "用户名不存在"
            }
        }), 401
    elif not check_password_hash(user['password'], password):  # 验证密码
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_PASSWORD",
                "message": "密码错误"
            }
        }), 401
        
    # 生成令牌
    token = generate_token(user['id'])
    
    return jsonify({
        "ok": True,
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24小时（秒）
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "phone": user['phone'],
                "created_at": user['created_at'].isoformat()
            }
        }
    }), 200

# 登出接口
@auth_bp.route("/api/auth/logout", methods=["POST"])
@token_required
def logout():
    session.pop('user_id', None)  # 清除session
    return jsonify({"ok": True}), 200

# 获取当前用户信息
@auth_bp.route("/api/auth/me", methods=["GET"])
@token_required
def get_current_user():
    user = User.find_by_id(session['user_id'])
    if not user:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "用户不存在"
            }
        }), 404
        
    return jsonify({
        "ok": True,
        "data": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "phone": user['phone'],
            "created_at": user['created_at'].isoformat()
        }
    }), 200