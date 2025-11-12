import sqlite3
from flask import g, current_app

class BoyaDatabase():
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.teardown_appcontext(self.close_db)
        self.db_path = app.config['DATABASE']

    def get_db(self):
        if 'db' not in g:
            g.db = sqlite3.connect(self.db_path)
            g.db.row_factory = sqlite3.Row
        return g.db

    def close_db(self, e=None):
        db:sqlite3.Connection = g.pop('db', None)
        if db is not None:
            db.close()