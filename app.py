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

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')


def _utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=_utcnow)

    games_created = db.relationship('Game', backref='creator', lazy='dynamic', foreign_keys='Game.creator_id')
    participations = db.relationship('GamePlayer', backref='player', lazy='dynamic')

    def set_password(self, password):
        import hashlib
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        import hashlib
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    from datetime import datetime, timezone

# ... existing code stays the same

    def has_active_game(self):
        try:
            from datetime import datetime
            now = datetime.utcnow()
            return Game.query.join(GamePlayer).filter(
                GamePlayer.user_id == self.id,
                Game.start_time > now,
                Game.status == 'scheduled'
            ).first() is not None
        except Exception:
            return False

    def has_created_game(self):
        try:
            from datetime import datetime
            now = datetime.utcnow()
            return Game.query.filter(
                Game.creator_id == self.id,
                Game.start_time > now,
                Game.status == 'scheduled'
            ).first() is not None
        except Exception:
            return False


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    players = db.relationship('GamePlayer', backref='game', lazy='dynamic', cascade='all, delete-orphan')

    def get_player_count(self):
        return self.players.count()

    def is_full(self):
        return self.get_player_count() >= 4


class GamePlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    team = db.Column(db.String(20))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


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
            
            db.create_all()
    except Exception as e:
        app.logger.error(f"DB init error: {e}")


@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory('static', 'favicon.ico')


import routes

handler = app