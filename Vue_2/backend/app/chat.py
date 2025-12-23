import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from .auth import token_required
from .models import Message, Conversation, User, Item
from datetime import datetime
import jwt
from flask import current_app

chat_bp = Blueprint("chat", __name__)

# 存储用户socket连接映射 {user_id: sid}
user_sockets = {}

def verify_socket_token(token):
    """验证Socket连接的JWT token并返回user_id"""
    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=['HS256']
        )
        return payload['sub']
    except:
        return None


# ============= SocketIO 事件处理 =============

def register_socketio_events(socketio):
    """注册SocketIO事件处理器（需要在__init__.py中调用）"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """客户端连接事件"""
        logger.info(f"Client attempting to connect, auth: {auth}")
        
        token = auth.get('token') if auth else None
        if not token:
            logger.warning("Connection rejected: no token provided")
            return False
        
        user_id = verify_socket_token(token)
        if not user_id:
            logger.warning("Connection rejected: invalid token")
            return False
        
        # 记录用户socket连接
        user_sockets[user_id] = request.sid
        
        # 只加入用户专属房间
        join_room(f"user_{user_id}")
        
        logger.info(f"User {user_id} connected with sid {request.sid}")
        emit('connected', {'user_id': user_id, 'message': '连接成功'})
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接事件"""
        user_id = None
        for uid, sid in list(user_sockets.items()):
            if sid == request.sid:
                user_id = uid
                del user_sockets[uid]
                break
        
        if user_id:
            leave_room(f"user_{user_id}")
            logger.info(f"User {user_id} disconnected")
        else:
            logger.info(f"Unknown client disconnected: {request.sid}")
    
    
    # 简化版：通过 user room 实现正在输入
    @socketio.on('typing')
    def handle_typing(data):
        """用户正在输入的状态通知"""
        to_user_id = data.get('to_user_id')  # 改为接收 to_user_id
        user_id = data.get('user_id')
        item_id = data.get('item_id')  # 用于前端判断是哪个会话
        is_typing = data.get('is_typing', True)
        
        if to_user_id:
            # 直接推送给对方的 user room
            emit('user_typing', {
                'user_id': user_id,
                'item_id': item_id,  # 前端用这个判断是否显示
                'is_typing': is_typing
            }, room=f"user_{to_user_id}")


# ----- HTTP API -----

@chat_bp.route("/api/messages", methods=["POST"])
@token_required
def send_message():
    """发送消息"""
    from app import socketio
    
    data = request.get_json()
    to_user_id = data.get('to_user_id')
    item_id = data.get('item_id')
    content = data.get('content')
    
    # 参数验证
    if not to_user_id or not item_id or not content:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "接收用户ID、商品ID和消息内容不能为空"
            }
        }), 400
    
    try:
        to_user_id = int(to_user_id)
        item_id = int(item_id)
    except (ValueError, TypeError):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "用户ID或商品ID格式错误"
            }
        }), 400
    
    # 检查接收用户是否存在
    user = User.find_by_id(to_user_id)
    if not user:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "接收用户不存在"
            }
        }), 404
    
    # 检查商品是否存在
    item = Item.find_by_id(item_id)
    if not item:
        return jsonify({
            "ok": False,
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "商品不存在"
            }
        }), 404
    
    # 不能给自己发消息
    if session['user_id'] == to_user_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_OPERATION",
                "message": "不能给自己发送消息"
            }
        }), 400
    
    try:
        # 发送消息
        message_data = Message.send(session['user_id'], to_user_id, item_id, content)
        
        # 构造返回数据
        response_data = {
            "id": message_data['id'],
            "conversation_id": message_data['conversation_id'],
            "from_user_id": session['user_id'],
            "to_user_id": to_user_id,
            "item_id": item_id,
            "content": content,
            "created_at": message_data['created_at']
        }
        
        # 简化：只推送到接收方的 user room
        socketio.emit('new_message', response_data, room=f"user_{to_user_id}")
        
        logger.info(f"Message sent from {session['user_id']} to {to_user_id}, pushed via SocketIO")
        
        return jsonify({
            "ok": True,
            "data": response_data
        }), 201
    except Exception as e:
        logger.exception("发送消息失败")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SEND_FAILED",
                "message": f"发送消息失败: {str(e)}"
            }
        }), 500


@chat_bp.route("/api/messages/conversations")
@token_required
def get_conversations():
    """获取当前用户的所有会话列表"""
    try:
        conversations = Conversation.get_user_conversations(session['user_id'])
        return jsonify({
            "ok": True,
            "data": conversations
        }), 200
    except Exception as e:
        logger.exception("获取会话列表失败")
        return jsonify({
            "ok": False,
            "error": {
                "code": "FETCH_FAILED",
                "message": "获取会话列表失败"
            }
        }), 500


@chat_bp.route("/api/messages/conversations/<int:other_user_id>/<int:item_id>")
@token_required
def get_chat_history(other_user_id, item_id):
    """获取与指定用户关于指定商品的聊天记录"""
    # 检查商品是否存在
    item = Item.find_by_id(item_id)
    if not item:
        return jsonify({
            "ok": False,
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "Product not exists"
            }
        }), 404
    
    # 检查对方用户是否存在
    other_user = User.find_by_id(other_user_id)
    if not other_user:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not exists"
            }
        }), 404
    
    try:
        messages = Message.get_conversation(session['user_id'], other_user_id, item_id)
        print("get_chat_history messages:", messages)
        return jsonify({
            "ok": True,
            "data": messages
        })
    except Exception as e:
        logger.exception("Fail to get chat history")
        return jsonify({
            "ok": False,
            "error": {
                "code": "FETCH_FAILED",
                "message": "Fail to get chat history"
            }
        }), 500

@chat_bp.route("/api/messages/conversations/<int:conversation_id>/read", methods=["POST"])
@token_required
def set_read_status(conversation_id):
    data = request.get_json()
    other_user_id = data.get('other_user_id')
    item_id = data.get('item_id')

    # 检查商品是否存在
    item = Item.find_by_id(item_id)
    if not item:
        return jsonify({
            "ok": False,
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "Product not exists"
            }
        }), 404
    
    # 检查对方用户是否存在
    other_user = User.find_by_id(other_user_id)
    if not other_user:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not exists"
            }
        }), 404
    
    try:
        messages = Message.get_conversation(session['user_id'], other_user_id, item_id)
        print("read_status_set:", messages)
        return jsonify({
            "ok": True,
            "conversation_id": conversation_id,
            "read_all": True
        }), 200
    except Exception as e:
        logger.exception("Fail to get chat history")
        return jsonify({
            "ok": False,
            "error": {
                "code": "FETCH_FAILED",
                "message": "Fail to get chat history"
            }
        }), 500