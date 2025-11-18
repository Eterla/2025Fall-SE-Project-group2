import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify, session
from .auth import token_required
from .models import Message, Conversation, User, Item
from datetime import datetime

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/messages", methods=["POST"])
@token_required
def send_message():
    """发送消息"""
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
        message_id = Message.send(session['user_id'], to_user_id, item_id, content)
        
        return jsonify({
            "ok": True,
            "data": {
                "id": message_id,
                "from_user_id": session['user_id'],
                "to_user_id": to_user_id,
                "item_id": item_id,
                "content": content,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201
    except Exception as e:
        logger.exception("发送消息失败")
        return jsonify({
            "ok": False,
            "error": {
                "code": "SEND_FAILED",
                "message": "发送消息失败"
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
        })
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