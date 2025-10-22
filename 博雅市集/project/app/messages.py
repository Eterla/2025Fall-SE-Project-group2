from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .auth import login_required
from .models import Chat, User, Item

messages_bp = Blueprint("messages", __name__)

@messages_bp.route("/messages")
@login_required
def messages():
    convos = Chat.conversations_for_user(session["user_id"])
    return render_template("messages.html", chats=convos)

@messages_bp.route("/send_message/<int:seller_id>/<int:item_id>", methods=["GET", "POST"])
@login_required
def send_message(seller_id, item_id):
    seller = User.find_by_id(seller_id)
    if not seller:
        flash("卖家不存在")
        return redirect(url_for("main.index"))
    item = Item.get_by_id(item_id)
    if not item:
        flash("商品不存在")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            Chat.send_message(session["user_id"], seller_id, item_id, content)
            flash("消息发送成功")
        return redirect(url_for("messages.chat_detail", other_user_id=seller_id, item_id=item_id))
    # redirect to chat view for GET
    return redirect(url_for("messages.chat_detail", other_user_id=seller_id, item_id=item_id))

@messages_bp.route("/chat_detail/<int:other_user_id>/<int:item_id>")
@login_required
def chat_detail(other_user_id, item_id):
    other = User.find_by_id(other_user_id)
    if not other:
        flash("用户不存在")
        return redirect(url_for("messages.messages"))
    item = Item.get_by_id(item_id)
    if not item:
        flash("商品不存在")
        return redirect(url_for("messages.messages"))

    msgs = Chat.messages_between(session["user_id"], other_user_id, item_id)
    return render_template("chat_detail.html", other_user=other, item=item, messages=msgs)

@messages_bp.route("/send_message_detail/<int:receiver_id>/<int:item_id>", methods=["POST"])
@login_required
def send_message_detail(receiver_id, item_id):
    content = request.form.get("content", "").strip()
    receiver = User.find_by_id(receiver_id)
    if not receiver:
        flash("接收者不存在")
        return redirect(url_for("messages.messages"))
    item = Item.get_by_id(item_id)
    if not item:
        flash("商品不存在")
        return redirect(url_for("messages.messages"))
    if content:
        Chat.send_message(session["user_id"], receiver_id, item_id, content)
    return redirect(url_for("messages.chat_detail", other_user_id=receiver_id, item_id=item_id))