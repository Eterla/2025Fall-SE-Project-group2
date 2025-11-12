import logging
logger = logging.getLogger(__name__)
import os

from flask import Blueprint, request, jsonify, session, current_app
from .auth import token_required  # 修改为新的装饰器
from .models import Item, Favorite, Message, User
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

from utils import make_response_ok, error_response, make_response_api
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    # return api info
    return make_response_ok({"message": "Welcome to the Marketplace API: Backend is running."})

# 修改：首页商品列表API
@main_bp.route("/api/items")
def index():
    # q 
    q = request.args.get("search", "")

    items = Item.search_available(q)
    return jsonify({
        "ok": True,
        "data": items
    })

# 修改：发布商品API
@main_bp.route("/api/items", methods=["POST"])
@token_required
def publish():
    # 处理表单数据（支持文件上传）
    title = request.form.get("title", "")
    description = request.form.get("description", "")
    price = request.form.get("price", "0")
    tags = request.form.get("tags", "")
    image = request.files.get("image")
    
    if not title:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "商品标题不能为空"
            }
        }), 400
        
    try:
        price_val = float(price) if price else 0.0
    except ValueError:
        price_val = 0.0

    item_id = Item.publish(session["user_id"], title, description, price_val, tags, image)
    return jsonify({
        "ok": True,
        "data": {
            "id": item_id,
            "seller_id": session["user_id"],
            "title": title
        }
    }), 201

# 修改：商品详情API
@main_bp.route("/api/items/<int:item_id>")
def item_detail(item_id):
    logger.debug(f"Successfully received request for item ID: {item_id}")
    item = Item.find_by_id(item_id)
    if not item:
        return jsonify({
            "ok": False,
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "商品不存在"
            }
        }), 404
        
    # 检查是否已收藏
    is_favorite = False

    if 'user_id' in session:
        is_favorite = Favorite.is_favorite(session['user_id'], item_id)
    
    return jsonify({
        "ok": True,
        "data": {
            **item,
            "is_favorite": is_favorite
        }
    })

# 新增：获取用户发布的商品
@main_bp.route("/api/user/items")
@token_required
def user_items():
    items = Item.find_by_user(session['user_id'])
    return jsonify({
        "ok": True,
        "data": items
    })

# 新增：下架商品
@main_bp.route("/api/items/<int:item_id>/status", methods=["PUT"])
@token_required
def update_item_status(item_id):
    item = Item.find_by_id(item_id)
    if not item:
        return jsonify({
            "ok": False,
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "商品不存在"
            }
        }), 404
    
    # 检查是否是商品的卖家
    if item['seller_id'] != session['user_id']:
        return jsonify({
            "ok": False,
            "error": {
                "code": "PERMISSION_DENIED",
                "message": "无权操作此商品"
            }
        }), 403
    
    data = request.get_json()
    status = data.get('status', 'sold')
    
    if status not in ['available', 'sold', 'reserved']:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_STATUS",
                "message": "无效的商品状态"
            }
        }), 400
    
    success = Item.update_status(item_id, status)
    if success:
        return jsonify({
            "ok": True,
            "data": {
                "id": item_id,
                "status": status
            }
        })
    else:
        return jsonify({
            "ok": False,
            "error": {
                "code": "UPDATE_FAILED",
                "message": "更新商品状态失败"
            }
        }), 500

# 新增：收藏商品
@main_bp.route("/api/favorites", methods=["POST"])
@token_required
def add_favorite():
    logger.debug("add_favorite is invoked")
    data = request.get_json()
    item_id = data.get('item_id')
    
    if not item_id:
        logger.warning("item_id is missing in request")
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "商品ID不能为空"
            }
        }), 400
    
    # 检查商品是否存在
    item = Item.find_by_id(item_id)
    if not item:
        logger.warning(f"Item not found: {item_id}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "商品不存在"
            }
        }), 404
    logger.debug(f"Item found: {item_id}, proceeding to add favorite")
    success = Favorite.add(session['user_id'], item_id)
    return jsonify({
        "ok": True,
        "data": {
            "is_favorite": success,
            "item_id": item_id
        }
    })

# 新增：取消收藏
@main_bp.route("/api/favorites/<int:item_id>", methods=["DELETE"])
@token_required
def remove_favorite(item_id):
    success = Favorite.remove(session['user_id'], item_id)
    return jsonify({
        "ok": True,
        "data": {
            "is_favorite": False,
            "item_id": item_id
        }
    })

# 新增：获取收藏列表
@main_bp.route("/api/favorites")
@token_required
def get_favorites():
    favorites = Favorite.get_user_favorites(session['user_id'])
    return jsonify({
        "ok": True,
        "data": favorites
    })

# ADD:(wzy) Check favorite status API
@main_bp.route("/api/favorites/check", methods=["GET"])
def check_favorite_status():

    return jsonify({

    })
# 新增：发送消息
@main_bp.route("/api/messages", methods=["POST"])
@token_required
def send_message():
    data = request.get_json()
    to_user_id = data.get('to_user_id')
    item_id = data.get('item_id')
    content = data.get('content')
    
    if not to_user_id or not item_id or not content:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "接收用户ID、商品ID和消息内容不能为空"
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
    
    message_id = Message.send(session['user_id'], to_user_id, item_id, content)
    return jsonify({
        "ok": True,
        "data": {
            "id": message_id,
            "from_user_id": session['user_id'],
            "to_user_id": to_user_id,
            "item_id": item_id,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
    }), 201

# 新增：获取消息列表
@main_bp.route("/api/messages/conversations")
@token_required
def get_conversations():
    conversations = Message.get_conversations(session['user_id'])
    return jsonify({
        "ok": True,
        "data": conversations
    })

# 新增：获取聊天记录
@main_bp.route("/api/messages/conversations/<int:other_user_id>/<int:item_id>")
@token_required
def get_chat_history(other_user_id, item_id):
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
    
    messages = Message.get_conversation(session['user_id'], other_user_id, item_id)
    return jsonify({
        "ok": True,
        "data": messages
    })
