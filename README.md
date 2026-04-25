# Padel Court - Система бронирования корта

Веб-приложение для бронирования падел корта с Telegram авторизацией.

## Функции

- ✅ Регистрация через Telegram аккаунт
- ✅ Создание игр с указанием времени и комментария
- ✅ Командная игра 2 на 2 (автоматическое распределение)
- ✅ Ограничение: 1 человек = 1 активная игра
- ✅ Ограничение: 1 человек = 1 создатель игры
- ✅ Присоединение к существующим играм
- ✅ Адаптивный интерфейс для мобильных устройств
- ✅ Telegram Web App для удобного доступа

## Требования

- Python 3.9+
- Telegram Bot Token

## Установка

1. Клонируйте репозиторий и перейдите в папку:
```bash
cd padel_court
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env`:
```env
FLASK_SECRET_KEY=ваш-секретный-ключ
TELEGRAM_BOT_TOKEN=ваш-токен-бота
WEBAPP_URL=https://your-domain.com/telegram_app.html
```

5. Создайте бота в Telegram через @BotFather и получите токен

6. Запустите приложение:
```bash
python run.py
```

7. Откройте `http://localhost:5000` в браузере

## Настройка Telegram Web App

1. Запустите бота:
```bash
python bot.py
```

2. Откройте @BotFather в Telegram

3. Выберите вашего бота → Menu → Edit Bot → Edit Menu Button

4. Выберите "Menu Button" → "Configure"

5. Выберите пункт меню "Open" или создайте новый

6. Выберите "Web App" и введите URL вашего приложения (нужно задеплоить)

7. После деплоя обновите URL в `.env` файле

## Деплой

Для деплоя на Vercel/Render:

1. Создайте `vercel.json`:
```json
{
  "build": "pip install -r requirements.txt",
  "output": "build",
  "routes": [
    { "src": "/(.*)", "dest": "/app.py" }
  ]
}
```

2. Или используйте Docker:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_SECRET_KEY=your-key
ENV TELEGRAM_BOT_TOKEN=your-token
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Структура проекта

```
padel_court/
├── app.py              # Main Flask app + DB models
├── routes.py           # API endpoints
├── run.py              # Entry point
├── bot.py              # Telegram bot
├── telegram_app.html   # Web App для Telegram
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/style.css  # Стили
│   └── js/app.js      # Frontend JS
└── templates/
    ├── base.html      # Базовый шаблон
    ├── index.html     # Главная страница
    └── login.html     # Страница входа
```

## API Endpoints

- `GET /api/games` - Список игр
- `POST /api/games` - Создать игру
- `GET /api/games/<id>` - Информация об игре
- `POST /api/games/<id>/join` - Присоединиться
- `POST /api/games/<id>/leave` - Покинуть игру
- `DELETE /api/games/<id>` - Удалить игру
- `POST /api/auth/telegram` - Telegram авторизация
- `GET /api/user/me` - Текущий пользователь

## Лицензия

MIT