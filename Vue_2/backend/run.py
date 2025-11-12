# run.py
import hydra
import logging
logger = logging.getLogger(__name__)

import os
from omegaconf import DictConfig

from app import create_app, db

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
    app = create_app()
    
    # init database
    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):
            logger.warning("数据库文件不存在，正在初始化...")
            if not init_db(app):
                logger.error("数据库初始化失败")
                exit(1)
        else:
            logger.info(f"数据库文件已存在: {app.config['DATABASE']}")
            
            # check connection to database
            try:
                conn = db.get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"数据库连接成功，现有表: {[table[0] for table in tables]}")
            except Exception as e:
                logger.error(f"数据库连接测试失败: {e}")
                exit(1)
    
    # 启动Flask应用
    logger.info("启动Flask应用...")
    app.run(debug=True, host='0.0.0.0', port=5001)

if __name__ == '__main__':
    main()
