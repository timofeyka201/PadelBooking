from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app import app, db, User, Game, GamePlayer
from datetime import datetime


def verify_telegram_data(data):
    return True


def get_user_from_request():
    telegram_id = request.headers.get('X-Telegram-ID')
    if not telegram_id:
        telegram_id = request.args.get('telegram_id')
    if not telegram_id:
        return None
    return User.query.filter_by(telegram_id=str(telegram_id)).first()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/telegram_app.html')
def telegram_app():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/api/auth/telegram', methods=['POST'])
def telegram_auth():
    try:
        data = request.get_json()
        telegram_id = str(data.get('id', ''))
        username = data.get('username', 'Unknown')
        first_name = data.get('first_name', '')

        user = User.query.filter_by(telegram_id=telegram_id).first()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            db.session.add(user)
            db.session.commit()

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
    telegram_id = request.headers.get('X-Telegram-ID')
    if not telegram_id:
        telegram_id = request.args.get('telegram_id')
    if not telegram_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.filter_by(telegram_id=str(telegram_id)).first()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
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
    current_user = get_user_from_request()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()

    if current_user.has_created_game():
        return jsonify({'error': 'Вы уже создали игру. Нельзя создавать больше одной активной игры.'}), 400

    start_time = datetime.fromisoformat(data['start_time'])
    end_time = datetime.fromisoformat(data['end_time'])

    game = Game(
        title=data['title'],
        description=data.get('description', ''),
        start_time=start_time,
        end_time=end_time,
        creator_id=current_user.id
    )
    db.session.add(game)
    db.session.commit()

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