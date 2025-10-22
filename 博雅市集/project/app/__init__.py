import os
from flask import Flask

from .db import Database

def create_app(config=None):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    # Basic configuration
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET", "dev-secret-key-change-in-production")
    
    # Create instance directory if it doesn't exist
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.setdefault("DATABASE_PATH", os.path.join(app.instance_path, "db.sqlite3"))
    
    if config:
        app.config.update(config)

    # attach Database instance to app
    app.db = Database(app.config["DATABASE_PATH"])
    app.db.initialize()

    # register blueprints (imported late to avoid circular imports)
    from .auth import auth_bp
    from .main import main_bp
    from .messages import messages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(messages_bp)

    # Ensure static/images exists
    os.makedirs(os.path.join(app.static_folder, "images"), exist_ok=True)

    return app