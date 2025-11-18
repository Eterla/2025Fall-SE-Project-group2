import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify, session
from flask_socketio import emit, join_room, leave_room, rooms
from .auth import token_required
from .models import Message, Conversation, User, Item
from datetime import datetime
import jwt
from flask import current_app

chat_bp = Blueprint("chat", __name__)

# 存储用户socket连接映射 {user_id: sid}
user_sockets = {}

# 如果后续发现该验证也被其他地方需要使用，可以考虑移到main.py的blueprint外部或者utils.py中
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
        
        # 验证token
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
        
        # 加入用户专属房间（用于接收消息）
        join_room(f"user_{user_id}")
        
        logger.info(f"User {user_id} connected with sid {request.sid}")
        emit('connected', {'user_id': user_id, 'message': '连接成功'})
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接事件"""
        # 从映射中移除
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
    
    
    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        """加入会话房间（用于实时接收该会话的消息）"""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f"conversation_{conversation_id}"
            join_room(room)
            logger.info(f"Client {request.sid} joined {room}")
            emit('joined_conversation', {'conversation_id': conversation_id})
    
    
    @socketio.on('leave_conversation')
    def handle_leave_conversation(data):
        """离开会话房间"""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f"conversation_{conversation_id}"
            leave_room(room)
            logger.info(f"Client {request.sid} left {room}")
            emit('left_conversation', {'conversation_id': conversation_id})
    
    
    @socketio.on('typing')
    def handle_typing(data):
        """用户正在输入的状态通知"""
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        is_typing = data.get('is_typing', True)
        
        if conversation_id:
            room = f"conversation_{conversation_id}"
            emit('user_typing', {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'is_typing': is_typing
            }, room=room, skip_sid=request.sid)


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
    
    # 类型转换和验证
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
        # 发送消息（会自动创建或更新会话）
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
        
        # 实时推送消息给接收方（通过SocketIO）
        socketio.emit('new_message', response_data, room=f"user_{to_user_id}")
        
        # 也推送到会话房间（如果有人在该会话页面）
        socketio.emit('new_message', response_data, room=f"conversation_{message_data['conversation_id']}")
        
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
                "message": "商品不存在"
            }
        }), 404
    
    # 检查对方用户是否存在
    other_user = User.find_by_id(other_user_id)
    if not other_user:
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "用户不存在"
            }
        }), 404
    
    try:
        messages = Message.get_conversation(session['user_id'], other_user_id, item_id)
        return jsonify({
            "ok": True,
            "data": messages
        })
    except Exception as e:
        logger.exception("获取聊天记录失败")
        return jsonify({
            "ok": False,
            "error": {
                "code": "FETCH_FAILED",
                "message": "获取聊天记录失败"
            }
        }), 500