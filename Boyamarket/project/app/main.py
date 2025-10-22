from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .auth import login_required
from .models import Item, User, Favorite

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    q = request.args.get("search", "")
    items = Item.search_available(q)
    return render_template("index.html", items=items, search_query=q)

@main_bp.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    if request.method == "POST":
        title = request.form.get("title", "")
        description = request.form.get("description", "")
        price = request.form.get("price", "0")
        tags = request.form.get("tags", "")
        image = request.files.get("image")
        try:
            price_val = float(price) if price else 0.0
        except ValueError:
            price_val = 0.0

        Item.publish(session["user_id"], title, description, price_val, tags, image)
        flash("商品发布成功")
        return redirect(url_for("main.index"))
    return render_template("publish.html")

@main_bp.route("/item/<int:item_id>")
def item_detail(item_id):
    item = Item.get_by_id(item_id)
    if not item:
        flash("商品不存在")
        return redirect(url_for("main.index"))
    seller = User.find_by_id(item["seller_id"]) if item.get("seller_id") else None
    is_favorite = False
    if "user_id" in session:
        is_favorite = Favorite.is_favorited(session["user_id"], item_id)
    return render_template("item_detail.html", item=item, seller=seller, is_favorite=is_favorite)

@main_bp.route("/user_center")
@login_required
def user_center():
    items = Item.items_by_seller(session["user_id"])
    return render_template("user_center.html", user_items=items)

@main_bp.route("/item/<int:item_id>/remove", methods=["POST"])
@login_required
def remove_item(item_id):
    if Item.remove(item_id, session["user_id"]):
        flash("商品已下架")
    else:
        flash("无权操作此商品")
    return redirect(url_for("main.user_center"))

@main_bp.route("/item/<int:item_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(item_id):
    if Favorite.is_favorited(session["user_id"], item_id):
        Favorite.remove(session["user_id"], item_id)
        flash("已取消收藏")
    else:
        Favorite.add(session["user_id"], item_id)
        flash("收藏成功")
    return redirect(url_for("main.item_detail", item_id=item_id))

@main_bp.route("/favorites")
@login_required
def favorites():
    favs = Favorite.favorites_for_user(session["user_id"])
    return render_template("favorites.html", favorite_items=favs)