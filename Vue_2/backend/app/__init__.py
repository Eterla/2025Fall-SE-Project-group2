import logging
logger = logging.getLogger(__name__)

import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from .boya_database import BoyaDatabase

db = BoyaDatabase()
socketio = SocketIO()

def create_app(test_config=None):
    
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'market.db'),
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static/images'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # 确保必要的文件夹存在
    try:
        os.makedirs(app.instance_path)
        logger.info(f"创建实例文件夹: {app.instance_path}")
    except OSError:
        pass

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.info(f"创建上传文件夹: {app.config['UPLOAD_FOLDER']}")
    except OSError:
        pass

    # 启用CORS
    CORS(app, supports_credentials=True, origins="*", async_mode='eventlet')

    # Init SocketIO（支持跨域）
    socketio.init_app(app, cors_allowed_origins="*")
    logger.info("SocketIO初始化完成")

    # 初始化数据库
    db.init_app(app)
    logger.info("数据库管理器初始化完成")

    # 注册蓝图
    from .auth import auth_bp
    from .main import main_bp
    from .chat import chat_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    logger.info("Flask应用创建完成（已注册 auth, main, chat 蓝图）")
    
    return app