# run.py
import hydra
import logging
logger = logging.getLogger(__name__)

import os
from omegaconf import DictConfig

from app import create_app, db, socketio

def init_db(app):
    """初始化数据库，创建所有必要的表"""
    # 确保实例文件夹存在
    os.makedirs(app.instance_path, exist_ok=True)
    
    db_path = app.config['DATABASE']
    logger.info(f"初始化数据库: {db_path}")
    
    # 读取并执行 schema.sql
    schema_path = 'app/schema.sql'
    if not os.path.exists(schema_path):
        logger.error(f"Schema文件不存在: {schema_path}")
        return False
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        # 在应用上下文中使用 BoyaDatabase 执行 SQL
        with app.app_context():
            conn = db.get_db()
            conn.executescript(schema)
            conn.commit()
            logger.info("数据库表创建成功")
            
            # 验证表是否创建成功
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.debug(f"数据库中的表: {[table[0] for table in tables]}")
        
        return True
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        return False

@hydra.main(version_base=None, config_path="conf", config_name="config1_wzy")
def main(cfg: DictConfig):
    logger.info("Starting Boya Market Backend with SocketIO support...")
    logger.info(f"Configuration: {cfg}")
    
    # 导入app和socketio
    from app import create_app, socketio
    from app.chat import register_socketio_events
    
    # Init Database

    # 创建Flask应用
    app = create_app()
    
    # 先尝试连接数据库，如果失败则初始化
    try:
        with app.app_context():
            conn = db.get_db()
            # 尝试查询一个表来验证连接
            conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            logger.info("数据库连接成功")
    except Exception as e:
        logger.warning(f"数据库连接失败，尝试初始化: {e}")
        if not init_db(app):
            logger.error("数据库初始化失败，无法继续")
            return
        else:
            logger.info("数据库初始化成功")

    # 注册SocketIO事件处理器
    register_socketio_events(socketio)
    logger.info("SocketIO事件处理器已注册")
    
    # 使用socketio.run启动（支持WebSocket）
    port = cfg.get('port', 5001)
    host = cfg.get('host', '127.0.0.1')
    debug = cfg.get('debug', True)
    
    logger.info(f"Server starting on {host}:{port} (debug={debug})")
    logger.info("WebSocket endpoint: ws://{host}:{port}/socket.io/")
    
    # 使用eventlet异步模式启动
    socketio.run(app, 
                 host=host, 
                 port=port, 
                 debug=debug
                )  # 开发环境允许

if __name__ == "__main__":
    main()
