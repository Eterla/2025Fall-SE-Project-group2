# app/favorite.py
from flask import Blueprint, request, jsonify, session
from .auth import token_required
from .models import Favorite, Item, User
from datetime import datetime

favorite_bp = Blueprint("favorite", __name__)

# 添加收藏
@favorite_bp.route("/api/items/<int:item_id>/favorite", methods=["POST"])
@token_required
def add_favorite(item_id):
    """
    收藏商品
    """
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
    
    # 检查用户是否在收藏自己的商品
    if item['seller_id'] == session['user_id']:
        return jsonify({
            "ok": False,
            "error": {
                "code": "CANNOT_FAVORITE_OWN_ITEM",
                "message": "不能收藏自己的商品"
            }
        }), 400
    
    # 添加收藏
    success = Favorite.add(session['user_id'], item_id)
    
    if success:
        return jsonify({
            "ok": True,
            "data": {
                "message": "收藏成功",
                "item_id": item_id,
                "user_id": session['user_id'],
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

# 取消收藏
@favorite_bp.route("/api/items/<int:item_id>/favorite", methods=["DELETE"])
@token_required
def remove_favorite(item_id):
    """
    取消收藏商品
    """
    success = Favorite.remove(session['user_id'], item_id)
    
    if success:
        return jsonify({
            "ok": True,
            "data": {
                "message": "取消收藏成功",
                "item_id": item_id,
                "user_id": session['user_id']
            }
        }), 200
    else:
        return jsonify({
            "ok": False,
            "error": {
                "code": "FAVORITE_NOT_FOUND",
                "message": "收藏记录不存在"
            }
        }), 404

# 获取用户的收藏列表
@favorite_bp.route("/api/favorites", methods=["GET"])
@token_required
def get_favorites():
    """
    获取用户的收藏列表
    """
    favorites = Favorite.get_user_favorites(session['user_id'])
    
    return jsonify({
        "ok": True,
        "data": favorites
    }), 200

# 检查是否已收藏某个商品
@favorite_bp.route("/api/items/<int:item_id>/favorite/status", methods=["GET"])
@token_required
def check_favorite_status(item_id):
    """
    检查当前用户是否已收藏指定商品
    """
    is_favorite = Favorite.is_favorite(session['user_id'], item_id)
    
    return jsonify({
        "ok": True,
        "data": {
            "item_id": item_id,
            "is_favorite": is_favorite
        }
    }), 200

# 批量获取收藏状态
@favorite_bp.route("/api/favorites/status", methods=["GET"])
@token_required
def get_favorites_status():
    """
    批量获取多个商品的收藏状态
    查询参数: item_ids - 逗号分隔的商品ID列表
    """
    item_ids_str = request.args.get('item_ids', '')
    if not item_ids_str:
        return jsonify({
            "ok": False,
            "error": {
                "code": "MISSING_ITEM_IDS",
                "message": "缺少商品ID参数"
            }
        }), 400
    
    try:
        item_ids = [int(id.strip()) for id in item_ids_str.split(',')]
    except ValueError:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_ITEM_IDS",
                "message": "商品ID格式不正确"
            }
        }), 400
    
    result = {}
    for item_id in item_ids:
        is_favorite = Favorite.is_favorite(session['user_id'], item_id)
        result[str(item_id)] = is_favorite
    
    return jsonify({
        "ok": True,
        "data": result
    }), 200