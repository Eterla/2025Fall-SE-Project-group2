# app/models.py
import os
import sys
from werkzeug.security import check_password_hash
import logging
import hydra
logger = logging.getLogger(__name__)

import sqlite3
import datetime
import uuid
from flask import g, current_app
from werkzeug.utils import secure_filename
from .exceptions import UsernameTakenError, InvalidPasswordError
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
            INSERT INTO users (username, password, email, phone, created_at, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password, email, phone, created_at, None))
        
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
        for k, v in dict(user).items():
            logger.debug(f"User field: {k} = {v}")
        if user:
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "phone": user['phone'],
                "created_at": user['created_at'],
                "avatar_url": user['avatar_url']
            }
        return None
    
    @staticmethod
    def update_profile(user_id, username, email):
        conn = db.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
        if cursor.fetchone():
            raise UsernameTakenError()
        
        cursor.execute("""
            UPDATE users 
            SET username = ?, email = ?
            WHERE id = ?
        """, (username, email, user_id))

        conn.commit()
    
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
        return {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "created_at": user['created_at']
        }
    
    @staticmethod
    def change_password(user_id, old, hashed_new):
        conn = db.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()

        if not check_password_hash(result['password'], old):
            raise InvalidPasswordError()

        cursor.execute("""
            UPDATE users 
            SET password = ?
            WHERE id = ?
        """, (hashed_new, user_id))
    
        conn.commit()
    
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
        return {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "created_at": user['created_at']
        }

    @staticmethod
    def reset_password(user_id, hashed_new):
        """无须提供旧密码，直接重置（用于忘记密码流程）。"""
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (hashed_new, user_id)
        )
        conn.commit()
        return True
    
    @staticmethod
    def upload_avatar(user_id, avatar):
        avatar_path = None
        upload_folder = os.path.join(current_app.root_path, 'static/images')
        os.makedirs(upload_folder, exist_ok=True)
            
        ext = secure_filename(avatar.filename).split('.')[-1]
        filename = f"avatar_{user_id}_{uuid.uuid4()}.{ext}"
        avatar_path = os.path.join('images', filename)
        avatar.save(os.path.join(upload_folder, filename))
        
        avatar_url = f"{avatar_path}"
        
        conn = db.get_db()
        cursor = conn.cursor()
        user = User.find_by_id(user_id)
        
        old_avatar_url = user['avatar_url'] if 'avatar_url' in user else None
        if old_avatar_url:
            old_path = old_avatar_url.replace('/static/', '')
            old_full_path = os.path.join(current_app.root_path, 'static', old_path)
            if os.path.exists(old_full_path):
                try:
                    os.remove(old_full_path)
                except Exception as e:
                    logger.warning(f"删除旧头像失败: {e}")
        
        cursor.execute(
            """UPDATE users 
               SET avatar_url = ?
               WHERE id = ?""",
            (avatar_url, user_id)
        )
        
        conn.commit()

        return avatar_url


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
        # Version2: integrate AI tags auto generate function:
        auto_tags = AI_interface.generate_tags(existing_tags=tags, img_path=os.path.join(upload_folder, filename) if image else None)

        # >>>TODO>>>: **Notice: 当前逻辑是直接替换掉原有的tags从而最小程度的减小对其他部分code的改动，但是效果并不一定理想**
        tags = auto_tags[:255] # ensure tags length limit to 255 characters
        # <<<TODO<<<  后续确定了修改逻辑之后删除这些多余的Annotations

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
               image_path, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                   FROM items
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
        
        # here is a json object representing the item
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
        logger.debug(f"Finding items for user ID: {user_id}")
        conn = db.get_db()
        items = conn.execute(
            """SELECT items.*
               FROM items
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
    
    @staticmethod
    def update_all(item_id, title, description, price, status, tags, image):
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
        # # Version2: integrate AI tags auto generate function:
        # auto_tags = AI_interface.generate_tags(existing_tags=tags, img_path=os.path.join(upload_folder, filename) if image else None)

        # # >>>TODO>>>: **Notice: 当前逻辑是直接替换掉原有的tags从而最小程度的减小对其他部分code的改动，但是效果并不一定理想**
        # tags = auto_tags[:255] # ensure tags length limit to 255 characters
        # # <<<TODO<<<  后续确定了修改逻辑之后删除这些多余的Annotations

        # item_id is auto-incremented, so don't need to specify it
        curr_time = datetime.datetime.now() 
        # convert time to string for sqlite3 compatibility
        # And at create time, update time is same as create time, so just use both below
        curr_time = curr_time.strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
                """UPDATE items 
                   SET title = ?, description = ?, price = ?, status = ?, tags = ?, updated_at = ?, image_path = ?
                   WHERE id = ?""",
                (title, description, price, status, tags, curr_time, image_path, item_id)
            )
        conn.commit()
    
    @staticmethod
    def delete(item_id):
        conn = db.get_db()
        conn.execute(
            "DELETE FROM items WHERE id = ?",
            (item_id,)
        )
        conn.commit()
        return True

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


class Conversation:
    """会话管理类 - 管理用户之间关于特定商品的对话"""
    
    @staticmethod
    def get_or_create(user1_id, user2_id, item_id):
        """获取或创建会话，确保 user1_id < user2_id 以保证唯一性"""
        conn = db.get_db()
        cursor = conn.cursor()
        
        # to ensure user1_id < user2_id
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        # try to find a existing conversation
        cursor.execute("""
            SELECT id FROM conversations 
            WHERE user1_id = ? AND user2_id = ? AND item_id = ?
        """, (user1_id, user2_id, item_id))
        
        row = cursor.fetchone()
        if row:
            return row['id']
        
        # create a new conversation
        curr_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO conversations 
            (user1_id, user2_id, item_id, last_updated, unread_count_user1, unread_count_user2)
            VALUES (?, ?, ?, ?, 0, 0)
        """, (user1_id, user2_id, item_id, curr_time))
        
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def update_on_new_message(conversation_id, from_user_id, message_id):
        """新消息发送时更新会话信息"""
        conn = db.get_db()
        cursor = conn.cursor()
        
        # get conversation participants
        cursor.execute("""
            SELECT user1_id, user2_id FROM conversations WHERE id = ?
        """, (conversation_id,))
        
        conv = cursor.fetchone()
        if not conv:
            return
        
        # ensure which user is sending the message and update unread counts
        if from_user_id == conv['user1_id']:
            # user1 发送，user2 未读+1
            cursor.execute("""
                UPDATE conversations 
                SET last_message_id = ?, 
                    last_updated = ?,
                    unread_count_user2 = unread_count_user2 + 1
                WHERE id = ?
            """, (message_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), conversation_id))
        else:
            # user2 发送，user1 未读+1
            cursor.execute("""
                UPDATE conversations 
                SET last_message_id = ?, 
                    last_updated = ?,
                    unread_count_user1 = unread_count_user1 + 1
                WHERE id = ?
            """, (message_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), conversation_id))
        
        conn.commit()
    
    @staticmethod
    def mark_as_read(user_id, other_user_id, item_id):
        """标记会话为已读（清零当前用户的未读计数）"""
        conn = db.get_db()
        
        # ensure the order of user IDs
        user1_id, user2_id = (user_id, other_user_id) if user_id < other_user_id else (other_user_id, user_id)
        
        # ensure which user's unread count to reset
        if user_id == user1_id:
            conn.execute("""
                UPDATE conversations 
                SET unread_count_user1 = 0
                WHERE user1_id = ? AND user2_id = ? AND item_id = ?
            """, (user1_id, user2_id, item_id))
        else:
            conn.execute("""
                UPDATE conversations 
                SET unread_count_user2 = 0
                WHERE user1_id = ? AND user2_id = ? AND item_id = ?
            """, (user1_id, user2_id, item_id))
        
        conn.commit()
    
    @staticmethod
    def get_user_conversations(user_id):
        """获取用户的所有会话列表"""
        conn = db.get_db()
        
        rows = conn.execute("""
            SELECT 
                c.id as conversation_id,
                CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END as other_user_id,
                c.item_id,
                u.username as other_username,
                i.title as item_title,
                i.image_path as item_image,
                i.status as item_status,
                c.last_updated as last_message_time,
                CASE WHEN c.user1_id = ? THEN c.unread_count_user1 ELSE c.unread_count_user2 END as unread_count,
                m.content as last_message_content
            FROM conversations c
            LEFT JOIN users u ON u.id = CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END
            LEFT JOIN items i ON i.id = c.item_id
            LEFT JOIN messages m ON m.id = c.last_message_id
            WHERE c.user1_id = ? OR c.user2_id = ?
            ORDER BY c.last_updated DESC
        """, (user_id, user_id, user_id, user_id, user_id)).fetchall()
        
        result = []
        for row in rows:
            result.append({
                'conversation_id': row['conversation_id'],
                'other_user_id': row['other_user_id'],
                'other_username': row['other_username'],
                'item_id': row['item_id'],
                'item_title': row['item_title'],
                'item_image': row['item_image'],
                'item_status': row['item_status'],
                'last_message_time': row['last_message_time'],
                'last_message_content': row['last_message_content'],
                'unread_count': row['unread_count'] or 0
            })
        
        return result


class Message:
    """消息类 - 处理用户之间的消息发送与读取"""
    
    @staticmethod
    def send(from_user_id, to_user_id, item_id, content):
        """发送消息（会自动创建或更新会话）"""
        conn = db.get_db()
        cursor = conn.cursor()
        
        # 获取或创建会话
        conversation_id = Conversation.get_or_create(from_user_id, to_user_id, item_id)
        
        # 插入消息
        curr_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages 
            (conversation_id, from_user_id, to_user_id, item_id, content, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (conversation_id, from_user_id, to_user_id, item_id, content, curr_time))
        
        message_id = cursor.lastrowid
        conn.commit()
        
        # 更新会话信息
        Conversation.update_on_new_message(conversation_id, from_user_id, message_id)
        
        logger.debug(f"Message sent: id={message_id}, conversation={conversation_id}")
        # return the message_data_package
        return {
            'id': message_id,
            'conversation_id': conversation_id,
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'item_id': item_id,
            'content': content,
            'is_read': False,
            'created_at': curr_time
        }
    
    @staticmethod
    def get_conversation(user_id, other_user_id, item_id):
        """获取两个用户之间关于某商品的聊天记录"""
        conn = db.get_db()
        
        messages = conn.execute("""
            SELECT 
                m.*,
                u1.username as from_username,
                u2.username as to_username
            FROM messages m
            JOIN users u1 ON m.from_user_id = u1.id
            JOIN users u2 ON m.to_user_id = u2.id
            WHERE 
                ((m.from_user_id = ? AND m.to_user_id = ?) OR 
                 (m.from_user_id = ? AND m.to_user_id = ?))
                AND m.item_id = ?
            ORDER BY m.created_at ASC
        """, (user_id, other_user_id, other_user_id, user_id, item_id)).fetchall()
        
        # 标记消息为已读（只标记发给当前用户的消息）
        conn.execute("""
            UPDATE messages 
            SET is_read = 1
            WHERE to_user_id = ? AND from_user_id = ? AND item_id = ? AND is_read = 0
        """, (user_id, other_user_id, item_id))
        conn.commit()
        
        # 更新会话未读计数
        Conversation.mark_as_read(user_id, other_user_id, item_id)
        
        result = []
        for msg in messages:
            result.append({
                'id': msg['id'],
                'conversation_id': msg['conversation_id'],
                'from_user_id': msg['from_user_id'],
                'to_user_id': msg['to_user_id'],
                'item_id': msg['item_id'],
                'content': msg['content'],
                'is_read': bool(msg['is_read']),
                'created_at': msg['created_at'],
                'from_username': msg['from_username'],
                'to_username': msg['to_username']
            })
        
        print(f"conversation ID : {messages[0]['conversation_id'] if messages else 'N/A'} between user {user_id} and user {other_user_id} about item {item_id} has {len(result)} messages.")

        return result


class AI_interface:
    def __init__(self):
        logger.warning("AI_interface: is initialized, notice that AI_interface now is a static placeholder class, so ensure that it's neccessary to instantiate it!")
    @staticmethod
    def generate_tags(existing_tags, img_path=None):
        # TODO: implement the hyperparameters to self class private members if necessary, [API-KEY, model_name, tags_scale, etc.]
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        MODEL_NAME = 'gemini-2.5-flash'  # placeholder for future use
        if GEMINI_API_KEY is None:
            logger.error("AI_interface: generate_tags is called without GEMINI_API_KEY environment variable set, so it will not work as expected!")
            return existing_tags
        '''
        generate_tags's Docs:
        this method generates additional tags based on existing tags and optional image input.
        After that, the item will have more comprehensive tags for better search and categorization.
        '''
        if img_path is not None:
            logger.info(f"AI_interface: generate_tags is called with image input: {img_path}")
            logger.warning("AI_interface: generate_tags with image input is not implemented yet!")
            pass
        tag_generate_prompt = \
        """
            You are an expert tag generator for online marketplace items. Given the existing tags for an item and the image of it(if given), generate additional relevant and specific tags that accurately describe the item to improve its discoverability.
            the generagted tags should be concise, relevant, and separated by a single space. And Notice that the tags could be in 中文 or English, it would be better if you can mix them properly according to the item type.
            because the tags will be used in an online marketplace platform, please ensure they are appropriate and useful for potential buyers searching for items.
            Here are some simplified rules to follow:(critical)
                1. Relevance: don't generate too much irrelevant tags, focus on the item's main features.
                2. Put the most promising and important tags at the beginning of your output, the less similar to the existing tags or item image, the later they should be placed into the tag list.
                3. Uniqueness: don't generate duplicate tags that have been already put into the generated tag list.
                4. the order need: Besides the rule2, also consider the different languages' tags order, e.g. 中文 tags should be placed before English tag.
                5. maybe some tags discribe the same concept but in different languages or formats, e.g. "笔记本电脑", "笔电", and "laptop", they all should be keeped, but must to Notice:
                    this is one of the most important rules: 'Keep the similar semantic tags in different languages or formats, but just put one of them at the prior list, the others should be put to the last to the list.'
                    This approach maximizes product search hit rates while preventing the tag list from appearing redundant. And since tags are displayed in a specific order, users typically only view the first few tags. Therefore, tags with identical meanings should be avoided appearing together at the front of the list. These other semantically similar auxiliary tags can be placed later to serve a supplementary function.
            example: 
                Existing tags: "银白色MacbookPro, 二手"
                Generated tags: "MacBookPro14英寸 二手 轻薄本 银白色 高性能 办公笔电 设计师电脑 laptop notebook silver-color used ......"
            Now, generate additional tags based on the following existing tags and image:
            Existing tags: {existing_tags}
        """.format(existing_tags=existing_tags)

        def gemini2_generate(api_key: str, prompt: str, json_output=True, img_path: str= None):
            model_name = MODEL_NAME
            time_retry = 0
            from google import genai
            from google.genai import types
            if img_path is None:
                logger.info("gemini2_generate: Generating tags without image input.")
                while time_retry <= 3:
                    try:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model= model_name,
                            contents=[
                                prompt
                            ]
                        )
                        curr_text = response.text
                        print("Generation is already done!")
                        print("The raw response text is: ", curr_text)
                        # pre-deal to ensure the json format
                        return curr_text
                    except Exception as e:
                        time_retry += 1
                        logger.error(f"gemini2_generate: Encountered error during generation without image: {e}, retry times: {time_retry}")
                        continue
            else:
                logger.info("gemini2_generate: Generating tags with image input.")
                with open(img_path, 'rb') as f:
                    image_bytes = f.read()
                response = None
                while time_retry <= 3:
                    try:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model = model_name,
                            contents=[
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type='image/jpeg',
                            ),
                            prompt
                            ]
                        )
                        curr_text = response.text
                        print("Generation is already done!")
                        print("The raw response text is: ", curr_text)
                        # pre-deal to ensure the json format
                        return curr_text
                    except Exception as e:
                        time_retry += 1
                        logger.error(f"gemini2_generate: Encountered error during generation with image: {e}, retry times: {time_retry}")
                        continue
            
        curr_text = gemini2_generate(api_key=GEMINI_API_KEY, prompt=tag_generate_prompt, img_path=img_path)
        # TODO: process the curr_text and existing_tags, and unique them, return the final tags, Maybe extract this function to a new number function in AI_interface class
        if curr_text is None:
            logger.error("AI_interface: generate_tags failed to get response from gemini2_generate, returning existing tags.")
            return existing_tags
        else:
            logger.info("AI_interface: generate_tags successfully got response from gemini2_generate.")
            return existing_tags + ' ' + curr_text.strip()
    
    def refine_tagstext2tags(self, tags):
        # Placeholder for future tag refinement logic
        # TODO: implement actual refinement logic, possibly using AI, temporarily just do nothing
        logger.error("AI_interface: refine_tagstext2tags is not implemented yet!")
        return None
    

if __name__ == "__main__":
    # for test purpose only

    ai = AI_interface()
    tags = ai.generate_tags(existing_tags="laptop, electronics, computer", img_path=None)
    print("Generated tags: ", tags)