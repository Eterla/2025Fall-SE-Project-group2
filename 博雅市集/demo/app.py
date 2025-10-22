from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import hashlib
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 实际使用时应设置更安全的密钥

# 确保目录存在
if not os.path.exists('static/images'):
    os.makedirs('static/images')

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建商品表
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        price REAL,
        tags TEXT,
        image_path TEXT,
        status TEXT DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (seller_id) REFERENCES users(id)
    )''')
    
    # 创建收藏表
    cursor.execute('''CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )''')
    
    # 创建聊天表
    cursor.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        item_id INTEGER,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )''')
    
    conn.commit()
    conn.close()

# 哈希密码函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 验证登录装饰器
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# 首页
@app.route('/')
def index():
    conn = get_db_connection()
    
    # 获取搜索关键词
    search_query = request.args.get('search', '')
    
    if search_query:
        # 搜索功能
        items = conn.execute(
            'SELECT * FROM items WHERE (title LIKE ? OR description LIKE ? OR tags LIKE ?) AND status = ? ORDER BY created_at DESC',
            (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', 'available')
        ).fetchall()
    else:
        # 获取所有可用商品
        items = conn.execute('SELECT * FROM items WHERE status = ? ORDER BY created_at DESC', ('available',)).fetchall()
    
    conn.close()
    return render_template('index.html', items=items, search_query=search_query)

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        
        conn = get_db_connection()
        
        # 检查用户名是否已存在
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('用户名已存在')
            conn.close()
            return redirect(url_for('register'))
        
        # 注册新用户
        conn.execute(
            'INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)',
            (username, hash_password(password), email, phone)
        )
        conn.commit()
        conn.close()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# 登出
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 发布商品
@app.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        tags = request.form['tags']
        
        # 处理图片上传
        image_path = None
        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            # 生成唯一文件名
            filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
            image_path = os.path.join('static/images', filename)
            image.save(image_path)
            # 存储相对路径
            image_path = image_path[7:]  # 移除'static/'前缀
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO items (seller_id, title, description, price, tags, image_path) VALUES (?, ?, ?, ?, ?, ?)',
            (session['user_id'], title, description, price, tags, image_path)
        )
        conn.commit()
        conn.close()
        
        flash('商品发布成功')
        return redirect(url_for('index'))
    
    return render_template('publish.html')

# 商品详情
@app.route('/item/<int:item_id>')
def item_detail(item_id):
    conn = get_db_connection()
    
    # 获取商品信息
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        flash('商品不存在')
        return redirect(url_for('index'))
    
    # 获取卖家信息
    seller = conn.execute('SELECT * FROM users WHERE id = ?', (item['seller_id'],)).fetchone()
    
    # 检查是否已收藏
    is_favorite = False
    if 'user_id' in session:
        favorite = conn.execute(
            'SELECT * FROM favorites WHERE user_id = ? AND item_id = ?',
            (session['user_id'], item_id)
        ).fetchone()
        is_favorite = favorite is not None
    
    conn.close()
    return render_template('item_detail.html', item=item, seller=seller, is_favorite=is_favorite)

# 用户中心
@app.route('/user_center')
@login_required
def user_center():
    conn = get_db_connection()
    
    # 获取用户发布的商品
    user_items = conn.execute(
        'SELECT * FROM items WHERE seller_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    return render_template('user_center.html', user_items=user_items)

# 下架商品
@app.route('/item/<int:item_id>/remove', methods=['POST'])
@login_required
def remove_item(item_id):
    conn = get_db_connection()
    
    # 检查商品是否属于当前用户
    item = conn.execute('SELECT * FROM items WHERE id = ? AND seller_id = ?', (item_id, session['user_id'])).fetchone()
    
    if item:
        conn.execute('UPDATE items SET status = ? WHERE id = ?', ('removed', item_id))
        conn.commit()
        flash('商品已下架')
    else:
        flash('无权操作此商品')
    
    conn.close()
    return redirect(url_for('user_center'))

# 添加/移除收藏
@app.route('/item/<int:item_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(item_id):
    conn = get_db_connection()
    
    # 检查是否已收藏
    favorite = conn.execute(
        'SELECT * FROM favorites WHERE user_id = ? AND item_id = ?',
        (session['user_id'], item_id)
    ).fetchone()
    
    if favorite:
        # 移除收藏
        conn.execute('DELETE FROM favorites WHERE id = ?', (favorite['id'],))
        flash('已取消收藏')
    else:
        # 添加收藏
        conn.execute('INSERT INTO favorites (user_id, item_id) VALUES (?, ?)', (session['user_id'], item_id))
        flash('收藏成功')
    
    conn.commit()
    conn.close()
    return redirect(url_for('item_detail', item_id=item_id))

# 收藏列表
@app.route('/favorites')
@login_required
def favorites():
    conn = get_db_connection()
    
    # 获取用户收藏的商品
    favorite_items = conn.execute(
        '''SELECT items.* FROM items
           JOIN favorites ON items.id = favorites.item_id
           WHERE favorites.user_id = ? AND items.status = 'available'
           ORDER BY favorites.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    return render_template('favorites.html', favorite_items=favorite_items)

# 消息列表
@app.route('/messages')
@login_required
def messages():
    conn = get_db_connection()
    
    # 获取用户参与的所有聊天会话（去重）
    chats = conn.execute(
        '''SELECT DISTINCT CASE 
               WHEN chats.sender_id = ? THEN chats.receiver_id
               ELSE chats.sender_id
           END as other_user_id,
           users.username as other_username,
           items.id as item_id,
           items.title as item_title,
           last_msg.content as content,
           last_msg.created_at as created_at
        FROM chats
        JOIN users ON (users.id = CASE 
            WHEN chats.sender_id = ? THEN chats.receiver_id
            ELSE chats.sender_id
        END)
        JOIN items ON items.id = chats.item_id
        JOIN (
            SELECT MAX(id) as max_id
            FROM chats
            WHERE sender_id = ? OR receiver_id = ?
            GROUP BY CASE 
                WHEN sender_id = ? THEN receiver_id
                ELSE sender_id
            END, item_id
        ) as msg_ids ON chats.id = msg_ids.max_id
        JOIN chats as last_msg ON last_msg.id = msg_ids.max_id
        WHERE chats.sender_id = ? OR chats.receiver_id = ?
        ORDER BY last_msg.created_at DESC''',
        (session['user_id'], session['user_id'], session['user_id'], session['user_id'], 
         session['user_id'], session['user_id'], session['user_id'])
    ).fetchall()
    
    conn.close()
    return render_template('messages.html', chats=chats)

# 发送消息（从商品详情页）
@app.route('/send_message/<int:seller_id>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def send_message(seller_id, item_id):
    conn = get_db_connection()
    
    # 检查卖家是否存在
    seller = conn.execute('SELECT * FROM users WHERE id = ?', (seller_id,)).fetchone()
    if not seller:
        conn.close()
        flash('卖家不存在')
        return redirect(url_for('index'))
    
    # 检查商品是否存在
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        flash('商品不存在')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        content = request.form['content']
        
        # 发送消息
        conn.execute(
            'INSERT INTO chats (sender_id, receiver_id, item_id, content) VALUES (?, ?, ?, ?)',
            (session['user_id'], seller_id, item_id, content)
        )
        conn.commit()
        conn.close()
        
        flash('消息发送成功')
        return redirect(url_for('chat_detail', other_user_id=seller_id, item_id=item_id))
    
    conn.close()
    # 重定向到聊天详情页
    return redirect(url_for('chat_detail', other_user_id=seller_id, item_id=item_id))

# 聊天详情
@app.route('/chat_detail/<int:other_user_id>/<int:item_id>')
@login_required
def chat_detail(other_user_id, item_id):
    conn = get_db_connection()
    
    # 获取对方用户信息
    other_user = conn.execute('SELECT * FROM users WHERE id = ?', (other_user_id,)).fetchone()
    if not other_user:
        conn.close()
        flash('用户不存在')
        return redirect(url_for('messages'))
    
    # 获取商品信息
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        flash('商品不存在')
        return redirect(url_for('messages'))
    
    # 获取聊天记录
    messages = conn.execute(
        '''SELECT * FROM chats 
           WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
           AND item_id = ?
           ORDER BY created_at ASC''',
        (session['user_id'], other_user_id, other_user_id, session['user_id'], item_id)
    ).fetchall()
    
    conn.close()
    return render_template('chat_detail.html', other_user=other_user, item=item, messages=messages)

# 在聊天详情页发送消息
@app.route('/send_message_detail/<int:receiver_id>/<int:item_id>', methods=['POST'])
@login_required
def send_message_detail(receiver_id, item_id):
    content = request.form['content']
    
    conn = get_db_connection()
    
    # 检查接收者是否存在
    receiver = conn.execute('SELECT * FROM users WHERE id = ?', (receiver_id,)).fetchone()
    if not receiver:
        conn.close()
        flash('接收者不存在')
        return redirect(url_for('messages'))
    
    # 检查商品是否存在
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        flash('商品不存在')
        return redirect(url_for('messages'))
    
    # 发送消息
    conn.execute(
        'INSERT INTO chats (sender_id, receiver_id, item_id, content) VALUES (?, ?, ?, ?)',
        (session['user_id'], receiver_id, item_id, content)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for('chat_detail', other_user_id=receiver_id, item_id=item_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
          