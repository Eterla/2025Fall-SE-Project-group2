# run.py
import hydra
import logging
logger = logging.getLogger(__name__)

import os
import re

from omegaconf import DictConfig


from app import create_app, db, socketio
from app.chat import register_socketio_events
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
    


    
    # Init Database

    # 创建Flask应用
    app = create_app()
    
    # Init database(use instance/market.db), if not exist or not correct according to schema.sql, recreate it
    # Init database(use instance/market.db), if not exist or not correct according to schema.sql, recreate it
    db_path = app.config.get('DATABASE')
    logger.info(f"Checking database at: {db_path}")

    need_init = False
    if not db_path or not os.path.exists(db_path):
        logger.info("Database file missing -> will initialize.")
        need_init = True
    else:
        try:
            schema_path = 'app/schema.sql'
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            # extract table names from CREATE TABLE statements
            table_names = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?([A-Za-z0-9_]+)["`]?', schema, flags=re.I)
            with app.app_context():
                conn = db.get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing = {row[0] for row in cursor.fetchall()}
            missing = [t for t in table_names if t not in existing]
            if missing:
                logger.warning(f"Missing tables {missing} -> will reinitialize database.")
                need_init = True
            else:
                logger.info("Database schema OK.")
        except Exception as e:
            logger.error(f"Error while verifying database schema: {e}. Will reinitialize.")
            need_init = True

    if need_init:
        try:
            if db_path and os.path.exists(db_path):
                os.remove(db_path)
                logger.info("Removed existing corrupted/old database file.")
        except Exception as e:
            logger.error(f"Failed to remove existing database file: {e}")
        if not init_db(app):
            logger.error("Database initialization failed. Exiting.")
            return

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
