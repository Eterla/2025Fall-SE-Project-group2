import os
import sqlite3
from flask import Flask, g
from flask_cors import CORS  # 新增：导入CORS解决跨域

def create_app(test_config=None):
    # 创建和配置应用
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',  # 开发环境密钥，生产环境需更换为随机安全密钥
        DATABASE=os.path.join(app.instance_path, 'market.db'),
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static/images'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 限制上传大小为16MB
    )

    if test_config is None:
        # 加载实例配置（如果存在）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 加载测试配置
        app.config.from_mapping(test_config)

    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 确保上传文件夹存在
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    # 启用CORS（解决前后端跨域问题）
    CORS(app, supports_credentials=True)  # 新增：允许跨域请求携带Cookie

    # 数据库连接管理（核心：供全应用使用的数据库连接工具）
    def get_db():
        if 'db' not in g:
            g.db = sqlite3.connect(
                app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row  # 支持按列名访问查询结果
        return g.db

    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # 初始化数据库（从schema.sql读取表结构）
    def init_db():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))

    @app.cli.command('init-db')
    def init_db_command():
        """清除现有数据并创建新表。"""
        init_db()
        print('Initialized the database.')

    # 注册蓝图（确保在数据库工具之后定义，避免导入时依赖问题）
    from .auth import auth_bp
    from .main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # 应用上下文结束时关闭数据库连接
    app.teardown_appcontext(close_db)

    return app