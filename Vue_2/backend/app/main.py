from flask import Blueprint, request, jsonify, session, current_app
from .auth import token_required  # 修改为新的装饰器
from .models import Item, Favorite, Message, User
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

main_bp = Blueprint("main", __name__)

# 获取用户公开信息（用于显示卖家）
@main_bp.route("/api/users/<int:user_id>")
def get_user_info(user_id):
    user = User.find_by_id(user_id)
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
            "created_at": user['created_at'].isoformat()
        }
    })

# 修改：首页商品列表API
@main_bp.route("/api/items")
def index():
    # 获取查询参数
    q = request.args.get("q", request.args.get("search", ""))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sort = request.args.get("sort", "created_at")
    status = request.args.get("status", "available")
    
    # 获取商品列表和总数
    items, total = Item.search_with_pagination(q, page, per_page, sort, status)
    
    return jsonify({
        "ok": True,
        "data": items,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
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

# 修改：部分更新商品（仅卖家）
@main_bp.route("/api/items/<int:item_id>", methods=["PATCH"])
@token_required
def update_item(item_id):
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
                "code": "FORBIDDEN",
                "message": "无权操作此商品"
            }
        }), 403
    
    # 处理表单数据或JSON数据
    if request.content_type and 'multipart/form-data' in request.content_type:
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        tags = request.form.get("tags")
        image = request.files.get("image")
    else:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        price = data.get("price")
        tags = data.get("tags")
        image = None
    
    # 更新商品信息
    updated_item = Item.update(item_id, title, description, price, tags, image)
    return jsonify({
        "ok": True,
        "data": updated_item
    })

# 修改：下架商品（逻辑删除）
@main_bp.route("/api/items/<int:item_id>", methods=["DELETE"])
@token_required
def delete_item(item_id):
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
                "code": "FORBIDDEN",
                "message": "无权操作此商品"
            }
        }), 403
    
    # 逻辑删除：设置状态为 'removed'
    success = Item.update_status(item_id, 'removed')
    if success:
        return '', 204  # No Content
    else:
        return jsonify({
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "删除失败"
            }
        }), 500

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
@main_bp.route("/api/items/<int:item_id>/favorite", methods=["POST"])
@token_required
def add_favorite(item_id):
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
    
    success = Favorite.add(session['user_id'], item_id)
    if success:
        return jsonify({
            "ok": True,
            "data": {
                "favorite_id": success,  # 假设返回收藏记录的ID
                "item_id": item_id,
                "created_at": datetime.now().isoformat()
            }
        }), 201
    else:
        return jsonify({
            "ok": False,
            "error": {
                "code": "ALREADY_FAVORITED",
                "message": "已经收藏过此商品"
            }
        }), 400

# 新增：取消收藏
@main_bp.route("/api/items/<int:item_id>/favorite", methods=["DELETE"])
@token_required
def remove_favorite(item_id):
    success = Favorite.remove(session['user_id'], item_id)
    if success:
        return '', 204  # No Content
    else:
        return jsonify({
            "ok": False,
            "error": {
                "code": "FAVORITE_NOT_FOUND",
                "message": "收藏记录不存在"
            }
        }), 404

# 新增：获取收藏列表
@main_bp.route("/api/favorites")
@token_required
def get_favorites():
    favorites = Favorite.get_user_favorites(session['user_id'])
    return jsonify({
        "ok": True,
        "data": favorites
    })

# 新增：获取消息列表（会话列表）
@main_bp.route("/api/messages")
@token_required
def get_conversations():
    conversations = Message.get_conversations(session['user_id'])
    return jsonify({
        "ok": True,
        "data": conversations
    })

# 新增：获取聊天记录
@main_bp.route("/api/messages/<int:other_user_id>/<int:item_id>")
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

# 新增：发送消息
@main_bp.route("/api/messages/<int:other_user_id>/<int:item_id>", methods=["POST"])
@token_required
def send_message(other_user_id, item_id):
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({
            "ok": False,
            "error": {
                "code": "EMPTY_MESSAGE",
                "message": "消息内容不能为空"
            }
        }), 400
    
    # 检查接收用户是否存在
    user = User.find_by_id(other_user_id)
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
    
    message_id = Message.send(session['user_id'], other_user_id, item_id, content)
    return jsonify({
        "ok": True,
        "data": {
            "id": message_id,
            "sender_id": session['user_id'],
            "receiver_id": other_user_id,
            "item_id": item_id,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
    }), 201
