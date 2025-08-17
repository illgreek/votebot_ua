import os
import json
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get('TELEGRAM_TOKEN', '8291861327:AAHt2Af8p53X9B0pwEbPxIFhOyX-jHroaps')
BOOKS_FILE = 'books.json'

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

def load_books():
    try:
        with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_books(books):
    with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Вітаю у книжному клубі!\n\n"
        "Ось доступні команди:\n"
        "/addbook Автор, Назва, Жанр — додати книгу\n"
        "/listbooks — переглянути список книг\n"
        "/poll — створити голосування вручну\n"
        "/start — показати цю інструкцію ще раз"
    )

def addbook(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text(
            "Будь ласка, використовуйте формат: /addbook Автор, Назва, Жанр"
        )
        return
    data = ' '.join(context.args)
    parts = [p.strip() for p in data.split(',')]
    if len(parts) < 3:
        update.message.reply_text(
            "Будь ласка, вкажіть автора, назву та жанр через кому. Наприклад: /addbook Джордж Орвелл, 1984, антиутопія"
        )
        return
    author, title, genre = parts[0], parts[1], parts[2]
    books = load_books()
    books.append({
        'author': author,
        'title': title,
        'genre': genre,
        'user': update.effective_user.full_name
    })
    save_books(books)
    update.message.reply_text(f'Книга "{title}" додана до списку!')

def listbooks(update: Update, context: CallbackContext):
    books = load_books()
    if not books:
        update.message.reply_text("Список книг порожній. Додайте першу книгу за допомогою /addbook!")
        return
    msg = "Список запропонованих книг:\n"
    for idx, book in enumerate(books, 1):
        msg += f"{idx}. {book['author']} — '{book['title']}' [{book['genre']}] (від {book['user']})\n"
    update.message.reply_text(msg)

def poll(update: Update, context: CallbackContext):
    books = load_books()
    if not books:
        update.message.reply_text("Список книг порожній. Додайте книги для голосування!")
        return
    options = [f"{b['title']} ({b['author']})" for b in books[:10]]
    if len(options) < 2:
        update.message.reply_text("Потрібно щонайменше 2 книги для голосування.")
        return
    context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question="Яку книгу читаємо наступною?",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False
    )

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('addbook', addbook))
dispatcher.add_handler(CommandHandler('listbooks', listbooks))
dispatcher.add_handler(CommandHandler('poll', poll))

CRON_SECRET = os.environ.get('CRON_SECRET', 'mysecret')

# Допоміжна функція для створення опитування
def create_poll(chat_id):
    books = load_books()
    if not books or len(books) < 2:
        return False
    options = [f"{b['title']} ({b['author']})" for b in books[:10]]
    bot.send_poll(
        chat_id=chat_id,
        question="Яку книгу читаємо наступною?",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False
    )
    return True

# Vercel handler

def handler(event, context):
    path = event.get('path', '')
    if event['httpMethod'] == 'POST':
        # Webhook від Telegram
        if path == '/api':
            body = json.loads(event['body'])
            update = Update.de_json(body, bot)
            dispatcher.process_update(update)
            return {
                'statusCode': 200,
                'body': 'ok'
            }
        # Cron endpoint
        elif path == '/api/cron':
            # Перевірка секрету
            params = event.get('queryStringParameters') or {}
            if params.get('secret') != CRON_SECRET:
                return {'statusCode': 403, 'body': 'Forbidden'}
            # Вкажіть chat_id вашої групи!
            chat_id = os.environ.get('CLUB_CHAT_ID')
            if not chat_id:
                return {'statusCode': 400, 'body': 'No chat_id'}
            ok = create_poll(chat_id)
            return {'statusCode': 200, 'body': 'poll sent' if ok else 'not enough books'}
    return {
        'statusCode': 405,
        'body': 'Method Not Allowed'
    }
