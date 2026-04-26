from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app import app, db, User, Game, GamePlayer
from datetime import datetime


def verify_telegram_data(data):
    return True


def get_user_from_request():
    from app import app
    user_id = request.headers.get('X-User-ID')
    app.logger.error(f"get_user_from_request: X-User-ID header = '{user_id}'")
    if not user_id:
        user_id = request.args.get('user_id')
    if not user_id:
        app.logger.error("get_user_from_request: no user_id found")
        return None
    user = User.query.get(int(user_id))
    app.logger.error(f"get_user_from_request: found user = {user}")
    return user


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/telegram_app.html')
def telegram_app():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/api/health')
def health():
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('user')]
        
        # Auto-add password_hash if missing
        if 'password_hash' not in columns:
            try:
                db.session.execute(text('ALTER TABLE "user" ADD COLUMN password_hash VARCHAR(200)'))
                db.session.commit()
            except: pass
        
        # Fix telegram_id to allow NULL - set default ''
        try:
            db.session.execute(text('UPDATE "user" SET telegram_id = \'\' WHERE telegram_id IS NULL'))
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN telegram_id SET DEFAULT \'\''))
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN telegram_id DROP NOT NULL'))
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Fix telegram_id error: {e}")
        
        result = db.session.execute(text('SELECT COUNT(*) FROM "user"')).scalar()
        return jsonify({'status': 'ok', 'users': result})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/auth/register', methods=['POST'])
def register():
    from app import app
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '')

        app.logger.error(f"REGISTER: username='{username}'")

        if not username or not password:
            return jsonify({'error': 'Введите имя пользователя и пароль'}), 400

        if len(password) < 4:
            return jsonify({'error': 'Пароль должен быть минимум 4 символа'}), 400

        # Check existing - filter out empty usernames
        existing = User.query.filter(User.username != None).filter_by(username=username).first()
        if existing:
            return jsonify({'error': 'Это имя пользователя уже занято'}), 400

        user = User(username=username, first_name=first_name)
        user.set_password(password)
        
        app.logger.error(f"REGISTER: adding user to session")
        db.session.add(user)
        db.session.commit()
        app.logger.error(f"REGISTER: committed, id={user.id}")

        return jsonify({'success': True, 'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name
        }})
    except Exception as e:
        app.logger.error(f"Register error: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    from app import app
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '')

        app.logger.error(f"REGISTER: username={username}")

        if not username or not password:
            return jsonify({'error': 'Введите имя пользователя и пароль'}), 400

        if len(password) < 4:
            return jsonify({'error': 'Пароль должен быть минимум 4 символа'}), 400

        existing = User.query.filter_by(username=username).first()
        if existing:
            return jsonify({'error': 'Это имя пользователя уже занято'}), 400

        user = User(username=username, first_name=first_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        app.logger.error(f"REGISTER: success id={user.id}")

        return jsonify({'success': True, 'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name
        }})
    except Exception as e:
        app.logger.error(f"Register error: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login_api():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401

        return jsonify({'success': True, 'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name
        }})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})


@app.route('/api/user/me')
def get_current_user():
    from app import app
    user_id = request.headers.get('X-User-ID')
    app.logger.error(f"/api/user/me: X-User-ID={user_id}")
    if not user_id:
        user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(int(user_id))
    if not user:
        app.logger.error(f"/api/user/me: user {user_id} not found")
        return jsonify({'error': 'Not authenticated'}), 401
    
    app.logger.error(f"/api/user/me: found user {user.id}, {user.username}")
    return jsonify({
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'has_active_game': user.has_active_game(),
        'has_created_game': user.has_created_game()
    })


from datetime import datetime, timezone


@app.route('/api/games')
def get_games():
    now = datetime.now(timezone.utc)
    games = Game.query.filter(Game.start_time > now).order_by(Game.start_time).all()
    return jsonify([{
        'id': g.id,
        'title': g.title,
        'description': g.description,
        'start_time': g.start_time.isoformat(),
        'end_time': g.end_time.isoformat(),
        'status': g.status,
        'creator': {
            'id': g.creator.id,
            'username': g.creator.username
        },
        'player_count': g.get_player_count(),
        'is_full': g.is_full(),
        'players': [{
            'id': p.player.id,
            'username': p.player.username,
            'team': p.team
        } for p in g.players]
    } for g in games])


@app.route('/api/games', methods=['POST'])
def create_game():
    from app import app
    current_user = get_user_from_request()
    app.logger.error(f"create_game: current_user = {current_user}")
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    app.logger.error(f"create_game: data = {data}")

    if current_user.has_created_game():
        return jsonify({'error': 'Вы уже создали игру. Нельзя создавать больше одной активной игры.'}), 400

    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except Exception as e:
        app.logger.error(f"create_game: date parse error: {e}")
        return jsonify({'error': 'Неверный формат даты'}), 400

    game = Game(
        title=data['title'],
        description=data.get('description', ''),
        start_time=start_time,
        end_time=end_time,
        creator_id=current_user.id
    )
    db.session.add(game)
    db.session.commit()
    app.logger.error(f"create_game: created game {game.id}")

    player = GamePlayer(user_id=current_user.id, game_id=game.id, team='creator')
    db.session.add(player)
    db.session.commit()

    return jsonify({'success': True, 'game_id': game.id})


@app.route('/api/games/<int:game_id>')
def get_game(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify({
        'id': game.id,
        'title': game.title,
        'description': game.description,
        'start_time': game.start_time.isoformat(),
        'end_time': game.end_time.isoformat(),
        'status': game.status,
        'creator': {
            'id': game.creator.id,
            'username': game.creator.username
        },
        'player_count': game.get_player_count(),
        'is_full': game.is_full(),
        'players': [{
            'id': p.player.id,
            'username': p.player.username,
            'team': p.team
        } for p in game.players]
    })


@app.route('/api/games/<int:game_id>/join', methods=['POST'])
def join_game(game_id):
    current_user = get_user_from_request()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401

    game = Game.query.get_or_404(game_id)

    if game.is_full():
        return jsonify({'error': 'Игра уже заполнена'}), 400

    existing = GamePlayer.query.filter_by(user_id=current_user.id, game_id=game_id).first()
    if existing:
        return jsonify({'error': 'Вы уже участвуете в этой игре'}), 400

    if current_user.has_active_game():
        return jsonify({'error': 'Вы уже участвуете в активной игре. Покинете текущую игру, чтобы присоединиться к новой.'}), 400

    team = 'team_a' if game.players.filter(GamePlayer.team == 'team_a').count() < 2 else 'team_b'
    player = GamePlayer(user_id=current_user.id, game_id=game_id, team=team)
    db.session.add(player)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/games/<int:game_id>/leave', methods=['POST'])
def leave_game(game_id):
    current_user = get_user_from_request()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401

    player = GamePlayer.query.filter_by(user_id=current_user.id, game_id=game_id).first()
    if not player:
        return jsonify({'error': 'Вы не участник этой игры'}), 400

    if player.team == 'creator' and current_user.id == Game.query.get(game_id).creator_id:
        return jsonify({'error': 'Создатель не может покинуть игру. Удалите игру.'}), 400

    db.session.delete(player)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    current_user = get_user_from_request()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401

    game = Game.query.get_or_404(game_id)

    if game.creator_id != current_user.id:
        return jsonify({'error': 'Только создатель может удалить игру'}), 400

    db.session.delete(game)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/games/my')
def my_games():
    current_user = get_user_from_request()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401

    created = Game.query.filter_by(creator_id=current_user.id).order_by(Game.start_time.desc()).all()
    participating = Game.query.join(GamePlayer).filter(
        GamePlayer.user_id == current_user.id
    ).order_by(Game.start_time.desc()).all()

    return jsonify({
        'created': [{
            'id': g.id,
            'title': g.title,
            'start_time': g.start_time.isoformat(),
            'status': g.status
        } for g in created],
        'participating': [{
            'id': g.id,
            'title': g.title,
            'start_time': g.start_time.isoformat(),
            'status': g.status
        } for g in participating]
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500