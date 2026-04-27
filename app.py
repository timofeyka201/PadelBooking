"""
Padel Court Booking System
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///padel_court.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@app.before_request
def run_migrations():
    with app.app_context():
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        try:
            if 'user' in tables:
                columns = [c['name'] for c in inspector.get_columns('user')]
                if 'password_hash' not in columns:
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN password_hash VARCHAR(200)'))
                    db.session.commit()
        except Exception as e:
            app.logger.error(f"Migration error: {e}")
        
        try:
            if 'game' in tables:
                game_columns = [c['name'] for c in inspector.get_columns('game')]
                app.logger.error(f"Current game columns: {game_columns}")
                if 'game_type' not in game_columns:
                    db.session.execute(text('ALTER TABLE "game" ADD COLUMN game_type VARCHAR(20) DEFAULT \'open\''))
                    db.session.commit()
                    app.logger.error("Added game_type column")
        except Exception as e:
            app.logger.error(f"Game migration error: {e}")
        
        try:
            if 'game_player' in tables:
                player_columns = [c['name'] for c in inspector.get_columns('game_player')]
                if 'approved' not in player_columns:
                    db.session.execute(text('ALTER TABLE "game_player" ADD COLUMN approved BOOLEAN DEFAULT false'))
                    db.session.commit()
        except Exception as e:
            app.logger.error(f"GamePlayer migration error: {e}")
        
        db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_db():
    try:
        with app.app_context():
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            try:
                if 'user' in tables:
                    columns = [c['name'] for c in inspector.get_columns('user')]
                    if 'password_hash' not in columns:
                        db.session.execute(text('ALTER TABLE "user" ADD COLUMN password_hash VARCHAR(200)'))
                        db.session.commit()
            except Exception as e:
                app.logger.error(f"Migration error: {e}")
            
            try:
                if 'game' in tables:
                    game_columns = [c['name'] for c in inspector.get_columns('game')]
                    app.logger.error(f"Current game columns: {game_columns}")
                    if 'game_type' not in game_columns:
                        db.session.execute(text('ALTER TABLE "game" ADD COLUMN game_type VARCHAR(20) DEFAULT \'open\''))
                        db.session.commit()
                        app.logger.error("Added game_type column")
            except Exception as e:
                app.logger.error(f"Game migration error: {e}")
            
            try:
                if 'game_player' in tables:
                    player_columns = [c['name'] for c in inspector.get_columns('game_player')]
                    if 'approved' not in player_columns:
                        db.session.execute(text('ALTER TABLE "game_player" ADD COLUMN approved BOOLEAN DEFAULT false'))
                        db.session.commit()
            except Exception as e:
                app.logger.error(f"GamePlayer migration error: {e}")
            
            db.create_all()
    except Exception as e:
        app.logger.error(f"DB init error: {e}")


@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory('public', 'favicon.ico')


import routes

handler = app