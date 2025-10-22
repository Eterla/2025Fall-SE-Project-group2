from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from .models import User

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@auth_bp.route("/register", methods=["GET", "POST"])
def register(): 
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email")
        phone = request.form.get("phone")

        if not username or not password:
            flash("用户名和密码为必填项")
            return redirect(url_for("auth.register"))

        existing = User.find_by_username(username)
        if existing:
            flash("用户名已存在")
            return redirect(url_for("auth.register"))

        User.create(username, password, email, phone)
        flash("注册成功，请登录")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = User.authenticate(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.index"))
        flash("用户名或密码错误")
        return redirect(url_for("auth.login"))
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))