import os
import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash  # 更安全的密码处理
from functools import wraps
import jwt
import datetime
from flask import current_app
# 在 auth.py 开头的导入部分添加
from .models import User  # 从当前目录的 models.py 中导入 User 类
from .exceptions import UsernameTakenError, InvalidPasswordError  # 从exceptions.py导入异常  <-- 修改这里
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
@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    logger.debug("Received registration request")
    data = request.get_json()
    
    # 验证必填参数
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "用户名, 密码, 邮箱都不能为空"
            }
        }), 400
        
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    logger.debug(f"Email received: {email}")
    phone = data.get('phone', '')
    logger.debug(f"Registering user: {username}, password:{password}, email: {email}, phone: {phone}")

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
        logger.info(f"User registered successfully: {username}")
        return jsonify({
            "ok": True,
            "data": {
                "id": new_user['id'],
                "username": new_user['username'],
                "email": new_user['email'],
                "created_at": new_user['created_at'] # NOTICE: Here returns a str, not a isoformat(), so fixed by removing .isoformat() ---wzy
            }
        }), 201
    except UsernameTakenError:
        logger.error(f"Username already taken: {username}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "USERNAME_TAKEN",
                "message": "用户名已被占用"
            }
        }), 409
    except Exception as e:
        # 捕获其他异常（如数据库错误）
        logger.error(f"Error during registration: {e}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "服务器内部错误"
            }
        }), 500

# 登录接口
@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    logger.debug("Received login request")
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
    logger.debug(f"Logging try: user: {username}, password:{password}")
    
    # 查询用户
    user = User.find_by_username(username)


    # 区分错误类型
    if not user:
        logger.info(f"User not found: {username}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "用户名不存在"
            }
        }), 401
    elif not check_password_hash(user['password'], password):  # 验证密码
        logger.info(f"Invalid password for user: {username}")
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
                "username": user['username']
            }
        }
    }), 200

# 忘记密码接口（生成一次性临时密码并重置）
@auth_bp.route("/api/auth/checkforpasswd", methods=["POST"])
def check_for_passwd():
    # 状态处在登陆前，不需要 token 验证
    import secrets
    import string

    logger.debug("Received password recovery request")
    data = request.get_json()
    # 验证必填参数
    if not data or not data.get('username') or not data.get('email'):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "用户名和邮箱不能为空"
            }
        }), 400

    username = data.get('username')
    email = data.get('email')
    logger.debug(f"Password recovery attempt for user: {username} with email: {email}")

    # 查询用户
    user = User.find_by_username(username)
    if not user or user['email'] != email:
        logger.info(f"Username and email do not match for user: {username}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_EMAIL_MISMATCH",
                "message": "用户名与邮箱不匹配"
            }
        }), 401

    # 生成一次性临时密码（不返回数据库中的加密密码）
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

    # 将临时密码写入数据库（以哈希形式保存）
    hashed_temp = generate_password_hash(temp_password, method='pbkdf2:sha256')
    try:
        User.reset_password(user['id'], hashed_temp)
    except Exception as e:
        logger.error(f"Failed to reset password for user {username}: {e}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "服务器内部错误"
            }
        }), 500

    logger.info(f"Temporary password generated for user: {username}")
    # 返回一次性临时密码，提示尽快修改
    return jsonify({
        "ok": True,
        "data": {
            "username": user['username'],
            "temporaryPassword": temp_password,
            "message": "已为您生成一次性临时密码，请使用其登录并尽快在个人中心修改。"
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

@auth_bp.route("/api/auth/update-profile", methods=["PUT"])
@token_required
def update_profile():
    data = request.get_json()
    
    # 验证必填参数
    if not data or not data.get('username') or not data.get('email'):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "用户名和邮箱不能为空"
            }
        }), 400
        
    username = data.get('username')
    email = data.get('email')
    
    try:
        updated_user = User.update_profile(session['user_id'], username, email)
        return jsonify({
            "ok": True,
        }), 201
    except UsernameTakenError:
        logger.error(f"Username already taken: {username}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "USERNAME_TAKEN",
                "message": "用户名已被占用"
            }
        }), 409
    except Exception as e:
        # 捕获其他异常（如数据库错误）
        logger.error(f"Error during registration: {e}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "服务器内部错误"
            }
        }), 500

@auth_bp.route("/api/auth/change-password", methods=["PUT"])
@token_required
def change_password():
    data = request.get_json()
    
    # 验证必填参数
    if not data or not data.get('currentPassword') or not data.get('newPassword'):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "密码不能为空"
            }
        }), 400
        
    old = data.get('currentPassword')
    new = data.get('newPassword')
    
    try:
        updated_user = User.change_password(session['user_id'], old, generate_password_hash(new, method='pbkdf2:sha256'))
        return jsonify({
            "ok": True,
        }), 201
    except InvalidPasswordError:
        logger.error(f"Current password wrong: {old}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "InvalidPassword",
                "message": "原密码错误"
            }
        }), 410
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "服务器内部错误"
            }
        }), 500

@auth_bp.route("/api/auth/upload-avatar", methods=["POST"])
@token_required
def upload_avatar():
    try:
        avatar = request.files.get("avatar")
    
        if not avatar:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "NO_FILE",
                    "message": "请选择头像文件"
                }
            }), 400
        
        avatar_url = User.upload_avatar(session["user_id"], avatar)

        return jsonify({
            "ok": True,
            "data": {
                "avatarUrl": avatar_url,
                "message": "头像上传成功"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"上传头像失败: {e}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "服务器内部错误"
            }
        }), 500