# app/models.py
import logging
import hydra
logger = logging.getLogger(__name__)

import sqlite3
import datetime
import os
import uuid
from flask import g, current_app
from werkzeug.utils import secure_filename
from .exceptions import UsernameTakenError
from app import db


class User:
    @staticmethod
    def create(username, password, email, phone):
        conn = db.get_db()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise UsernameTakenError()
        
        # 插入新用户
        created_at = datetime.datetime.now()
        cursor.execute("""
            INSERT INTO users (username, password, email, phone, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password, email, phone, created_at))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # 查询新用户信息并返回
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        return {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "created_at": user['created_at']
        }
    
    @staticmethod
    def find_by_username(username):
        conn = db.get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        
        if user:
            return {
                "id": user['id'],
                "username": user['username'],
                "password": user['password'],  # 返回加密后的密码用于验证
                "email": user['email'],
                "phone": user['phone'],
                "created_at": user['created_at']
            }
        return None
    
    @staticmethod
    def find_by_id(user_id):
        conn = db.get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        
        if user:
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "phone": user['phone'],
                "created_at": user['created_at']
            }
        return None


class Item:
    @staticmethod
    def publish(user_id, title, description, price, tags, image):
        logger.debug(f"Publishing item: user_id={user_id}, title={title}, price={price}, tags={tags}")
        conn = db.get_db()
        image_path = None
        if image:
            # 保存图片
            upload_folder = os.path.join(current_app.root_path, 'static/images')
            os.makedirs(upload_folder, exist_ok=True)
            
            # 生成唯一文件名
            ext = secure_filename(image.filename).split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            image_path = os.path.join('images', filename)
            
            # 保存文件
            image.save(os.path.join(upload_folder, filename))
        
        cursor = conn.cursor()
        # using user_id to get seller_name:
        user = User.find_by_id(user_id)
        seller_name = user['username'] if user else 'Unknown'
        # item_id is auto-incremented, so don't need to specify it
        curr_time = datetime.datetime.now() 
        # convert time to string for sqlite3 compatibility
        # And at create time, update time is same as create time, so just use both below
        curr_time = curr_time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            """INSERT INTO items (seller_id, seller_name, title, description, price, tags, 
               image_path, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, seller_name, title, description, price, tags, image_path, 'available', curr_time, curr_time) 
        )
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def search_available(query=''):
        conn = db.get_db()
        if query:
            logger.debug(f'query is required: {query}')
            items = conn.execute(
                """SELECT items.*
                   FORM items
                   WHERE items.status = 'available' AND 
                   (items.title LIKE ? OR items.description LIKE ? OR items.tags LIKE ?)
                   ORDER BY items.created_at DESC""",
                (f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchall()
        else:
            logger.debug('no query provided')
            items = conn.execute(
                """SELECT items.*
                   FROM items
                   WHERE items.status = 'available'
                   ORDER BY items.created_at DESC"""
            ).fetchall()
        
        # 转换为字典列表
        result = []
        for item in items:
            result.append({
                'id': item['id'],
                'seller_id': item['seller_id'],
                'seller_name': item['seller_name'],
                'title': item['title'],
                'description': item['description'],
                'price': item['price'],
                'tags': item['tags'],
                'image_path': item['image_path'],
                'status': item['status'],
                'created_at': item['created_at'],
                'updated_at': item['updated_at']
            })
        logger.debug(f"Search available items with query '{query}': found {len(result)} items")
        return result
    
    @staticmethod
    def find_by_id(item_id):

        conn = db.get_db()
        # before find, logout all items in database first
        # unlock items that were temporarily locked more than 24 hours ago
        try:
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
            conn.execute(
                "UPDATE items SET status = ?, updated_at = ? WHERE status = ? AND updated_at < ?",
                ('available', datetime.datetime.now(), 'locked', cutoff)
            )
            conn.commit()
        except Exception:
            logger.exception("Failed to cleanup locked items before find_by_id")

        logger.debug(f"Finding item by ID: {item_id}")
        item = conn.execute(
            """SELECT items.*
               FROM items
               WHERE items.id = ?""",
            (item_id,)
        ).fetchone()
        
        if not item:
            return None
        
        return {
            'id': item['id'],
            'seller_id': item['seller_id'],
            'seller_name': item['seller_name'],
            'title': item['title'],
            'description': item['description'],
            'price': item['price'],
            'tags': item['tags'],
            'image_path': item['image_path'],
            'status': item['status'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at']
        }
    
    @staticmethod
    def find_by_user(user_id):
        conn = db.get_db()
        items = conn.execute(
            """SELECT items.*, users.username as seller_name 
               FROM items JOIN users ON items.seller_id = users.id 
               WHERE items.seller_id = ?
               ORDER BY items.created_at DESC""",
            (user_id,)
        ).fetchall()
        
        result = []
        for item in items:
            result.append({
                'id': item['id'],
                'seller_id': item['seller_id'],
                'seller_name': item['seller_name'],
                'title': item['title'],
                'description': item['description'],
                'price': item['price'],
                'tags': item['tags'],
                'image_path': item['image_path'],
                'status': item['status'],
                'created_at': item['created_at'],
                'updated_at': item['updated_at']
            })
        
        return result
    
    @staticmethod
    def update_status(item_id, status):
        conn = db.get_db()
        try:
            conn.execute(
                "UPDATE items SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.datetime.now(), item_id)
            )
            conn.commit()
            return True
        except:
            return False

class Favorite:
    @staticmethod
    def add(user_id, item_id):
        conn = db.get_db()
        logger.debug(f"Favorite Class: Adding favorite: user_id={user_id}, item_id={item_id}")
        try:
            conn.execute(
                "INSERT INTO favorites (user_id, item_id, created_at) VALUES (?, ?, ?)",
                (user_id, item_id, datetime.datetime.now())
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 已经收藏过
            return False
    
    @staticmethod
    def remove(user_id, item_id):
        conn = db.get_db()
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
        conn.commit()
        return True
    
    @staticmethod
    def get_user_favorites(user_id):
        conn = db.get_db()
        favorites = conn.execute(
            """SELECT items.*, users.username as seller_name 
               FROM favorites 
               JOIN items ON favorites.item_id = items.id 
               JOIN users ON items.seller_id = users.id 
               WHERE favorites.user_id = ?
               ORDER BY favorites.created_at DESC""",
            (user_id,)
        ).fetchall()
        
        result = []
        for item in favorites:
            result.append({
                'id': item['id'],
                'seller_id': item['seller_id'],
                'seller_name': item['seller_name'],
                'title': item['title'],
                'description': item['description'],
                'price': item['price'],
                'tags': item['tags'],
                'image_path': item['image_path'],
                'status': item['status'],
                'created_at': item['created_at'],
                'updated_at': item['updated_at']
            })
        
        return result
    
    @staticmethod
    def is_favorite(user_id, item_id):
        conn = db.get_db()
        favorite = conn.execute(
            "SELECT * from favorites where user_id = ? and item_id = ?",
            (user_id, item_id)
        ).fetchone()
        return favorite is not None

class Message:
    @staticmethod
    def send(from_user_id, to_user_id, item_id, content):
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO messages (from_user_id, to_user_id, item_id, content, 
               is_read, created_at) VALUES (?, ?, ?, ?, ?, ?)""",
            (from_user_id, to_user_id, item_id, content, False, datetime.datetime.now())
        )
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_conversation(user_id, other_user_id, item_id):
        conn = db.get_db()
        messages = conn.execute(
            """SELECT messages.*, 
               u1.username as from_username, 
               u2.username as to_username 
               FROM messages 
               JOIN users u1 ON messages.from_user_id = u1.id 
               JOIN users u2 ON messages.to_user_id = u2.id 
               WHERE 
               ((messages.from_user_id = ? AND messages.to_user_id = ?) OR 
                (messages.from_user_id = ? AND messages.to_user_id = ?)) AND 
               messages.item_id = ?
               ORDER BY messages.created_at ASC""",
            (user_id, other_user_id, other_user_id, user_id, item_id)
        ).fetchall()
        
        # 标记为已读
        conn.execute(
            """UPDATE messages SET is_read = ? 
               WHERE to_user_id = ? AND from_user_id = ? AND item_id = ?""",
            (True, user_id, other_user_id, item_id)
        )
        conn.commit()
        
        result = []
        for msg in messages:
            result.append({
                'id': msg['id'],
                'from_user_id': msg['from_user_id'],
                'to_user_id': msg['to_user_id'],
                'item_id': msg['item_id'],
                'content': msg['content'],
                'is_read': msg['is_read'],
                'created_at': msg['created_at'],
                'from_username': msg['from_username'],
                'to_username': msg['to_username']
            })
        
        return result
    
    @staticmethod
    def get_conversations(user_id):
        conn = db.get_db()
        conversations = conn.execute(
            """SELECT DISTINCT 
               CASE WHEN from_user_id = ? THEN to_user_id ELSE from_user_id END as other_user_id,
               item_id,
               (SELECT username FROM users WHERE id = other_user_id) as other_username,
               (SELECT title FROM items WHERE id = item_id) as item_title,
               (SELECT image_path FROM items WHERE id = item_id) as item_image,
               (SELECT MAX(created_at) FROM messages 
                WHERE ((from_user_id = ? AND to_user_id = other_user_id) OR 
                       (from_user_id = other_user_id AND to_user_id = ?)) AND 
                      item_id = messages.item_id) as last_message_time,
               (SELECT COUNT(*) FROM messages 
                WHERE to_user_id = ? AND from_user_id = other_user_id AND 
                      item_id = messages.item_id AND is_read = 0) as unread_count
               FROM messages
               WHERE from_user_id = ? OR to_user_id = ?
               ORDER BY last_message_time DESC""",
            (user_id, user_id, user_id, user_id, user_id, user_id)
        ).fetchall()
        
        result = []
        for conv in conversations:
            result.append({
                'other_user_id': conv['other_user_id'],
                'other_username': conv['other_username'],
                'item_id': conv['item_id'],
                'item_title': conv['item_title'],
                'item_image': conv['item_image'],
                'last_message_time': conv['last_message_time'],
                'unread_count': conv['unread_count']
            })
        
        return result
