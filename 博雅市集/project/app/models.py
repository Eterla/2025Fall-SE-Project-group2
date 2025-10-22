import hashlib
import os
import uuid
from typing import Optional, List, Dict, Any
from flask import current_app
from werkzeug.utils import secure_filename

# Utility function to hash passwords
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class User:
    # Create a new user
    @classmethod
    def create(cls, username: str, password: str, email: str = None, phone: str = None) -> int:
        conn = current_app.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
            (username, _hash_password(password), email, phone)
        )
        conn.commit()
        user_id = cur.lastrowid # ID of the newly created user
        conn.close()
        return user_id
    
    # Find a user by username
    @classmethod
    def find_by_username(cls, username: str) -> Optional[dict]:
        conn = current_app.db.get_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        return dict(user) if user else None

    # Find a user by ID 
    @classmethod
    def find_by_id(cls, user_id: int) -> Optional[dict]:
        conn = current_app.db.get_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

    # Authenticate a user
    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[dict]:
        user = cls.find_by_username(username)
        if user and user["password"] == _hash_password(password):
            return user
        return None
    


class Item:
    # Publish a new item
    @classmethod
    def publish(cls, seller_id: int, title: str, description: str, price: float, tags: str, image_file=None) -> int:
        image_path = None   # default to None if no image is provided
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            extension = os.path.splitext(filename)[1] 
            unique = f"{uuid.uuid4().hex}{extension}" # generate unique filename 
            save_dir = os.path.join(current_app.static_folder, "images")
            os.makedirs(save_dir, exist_ok=True)
            full_path = os.path.join(save_dir, unique)
            image_file.save(full_path)
            
            # store relative path from static (for templates)
            image_path = f"images/{unique}"

        conn = current_app.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (seller_id, title, description, price, tags, image_path) VALUES (?, ?, ?, ?, ?, ?)",
            (seller_id, title, description, price, tags, image_path)
        )
        conn.commit()
        item_id = cur.lastrowid
        conn.close()
        return item_id

    @classmethod
    def get_by_id(cls, item_id: int) -> Optional[dict]:
        conn = current_app.db.get_connection()
        item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        conn.close()
        return dict(item) if item else None

    # Search available items by query
    @classmethod
    def search_available(cls, q: str = "") -> List[dict]:
        conn = current_app.db.get_connection()
        # If a query is provided, search in title, description, or tags
        if q:
            like = f"%{q}%" 

            # Only return available items
            rows = conn.execute(
                "SELECT * FROM items WHERE (title LIKE ? OR description LIKE ? OR tags LIKE ?) AND status = 'available' ORDER BY created_at DESC",
                (like, like, like)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM items WHERE status = 'available' ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # Get items by seller
    @classmethod
    def items_by_seller(cls, seller_id: int) -> List[dict]:
        conn = current_app.db.get_connection()
        rows = conn.execute("SELECT * FROM items WHERE seller_id = ? ORDER BY created_at DESC", (seller_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def remove(cls, item_id: int, seller_id: int) -> bool:
        conn = current_app.db.get_connection()
        cur = conn.cursor()
        # Mark the item as removed
        cur.execute("UPDATE items SET status = 'removed' WHERE id = ? AND seller_id = ?", (item_id, seller_id))
        conn.commit()
        updated = cur.rowcount > 0 # cur.rowcount tells how many rows were affected
        conn.close()
        return updated



class Favorite:
    # Check if an item is collected by a user
    @classmethod
    def is_favorite(cls, user_id: int, item_id: int) -> bool:
        conn = current_app.db.get_connection()
        fav = conn.execute("SELECT * FROM favorites WHERE user_id = ? AND item_id = ?", (user_id, item_id)).fetchone()
        conn.close()
        return fav is not None

    @classmethod
    def add(cls, user_id: int, item_id: int):
        conn = current_app.db.get_connection()
        conn.execute("INSERT INTO favorites (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
        conn.commit()
        conn.close()

    @classmethod
    def remove(cls, user_id: int, item_id: int):
        conn = current_app.db.get_connection()
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        conn.commit()
        conn.close()

    @classmethod
    def favorites_for_user(cls, user_id: int) -> List[dict]:
        conn = current_app.db.get_connection()
        rows = conn.execute(
            """SELECT items.* FROM items
               JOIN favorites ON items.id = favorites.item_id
               WHERE favorites.user_id = ? AND items.status = 'available'
               ORDER BY favorites.created_at DESC""",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]



class Chat:
    # Send a message from sender to receiver about an item
    @classmethod
    def send_message(cls, sender_id: int, receiver_id: int, item_id: int, content: str) -> int:
        conn = current_app.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chats (sender_id, receiver_id, item_id, content) VALUES (?, ?, ?, ?)",
            (sender_id, receiver_id, item_id, content)
        )
        conn.commit()
        msg_id = cur.lastrowid
        conn.close()
        return msg_id

    # Get messages between two users about a specific item
    @classmethod
    def messages_between(cls, user_a: int, user_b: int, item_id: int) -> List[dict]:
        conn = current_app.db.get_connection()
        rows = conn.execute(
            """SELECT * FROM chats
               WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
                 AND item_id = ?
               ORDER BY created_at ASC""",
            (user_a, user_b, user_b, user_a, item_id)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # Get recent conversations for a user
    @classmethod
    def conversations_for_user(cls, user_id: int) -> List[dict]:
        """
        返回用户的最近会话列表，每个会话包含对方用户信息、物品信息和最后一条消息内容及时间。
        """
        conn = current_app.db.get_connection()
        # For SQLite we build a query that finds the last message per (other_user, item)
        rows = conn.execute(
            """
            SELECT
              other_user.id AS other_user_id,
              other_user.username AS other_username,
              items.id AS item_id,
              items.title AS item_title,
              last_msg.content AS content,
              last_msg.created_at AS created_at
            FROM (
              SELECT
                CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END AS other_user_id,
                item_id,
                MAX(id) AS last_id
              FROM chats
              WHERE sender_id = ? OR receiver_id = ?
              GROUP BY other_user_id, item_id
            ) idx
            JOIN chats last_msg ON last_msg.id = idx.last_id
            JOIN users other_user ON other_user.id = idx.other_user_id
            JOIN items ON items.id = idx.item_id
            ORDER BY last_msg.created_at DESC
            """,
            (user_id, user_id, user_id)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]