import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, PollHandler
import json
from telegram.constants import ParseMode
from datetime import datetime, timedelta

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8291861327:AAHt2Af8p53X9B0pwEbPxIFhOyX-jHroaps'  # Замініть на свій токен

BOOKS_FILE = 'books.json'

def load_books():
    try:
        with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_books(books):
    with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю у книжному клубі!\n\n"
        "Ось доступні команди:\n"
        "/addbook Автор, Назва, Жанр — додати книгу\n"
        "/listbooks — переглянути список книг\n"
        "/poll — створити голосування вручну\n"
        "/setmonthlypoll — налаштувати щомісячне голосування\n"
        "/start — показати цю інструкцію ще раз"
    )

async def addbook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Будь ласка, використовуйте формат: /addbook Автор, Назва, Жанр"
        )
        return
    data = ' '.join(context.args)
    parts = [p.strip() for p in data.split(',')]
    if len(parts) < 3:
        await update.message.reply_text(
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
    await update.message.reply_text(f'Книга "{title}" додана до списку!')

async def listbooks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    books = load_books()
    if not books:
        await update.message.reply_text("Список книг порожній. Додайте першу книгу за допомогою /addbook!")
        return
    msg = "Список запропонованих книг:\n"
    for idx, book in enumerate(books, 1):
        msg += f"{idx}. {book['author']} — '{book['title']}' [{book['genre']}] (від {book['user']})\n"
    await update.message.reply_text(msg)

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    books = load_books()
    if not books:
        await update.message.reply_text("Список книг порожній. Додайте книги для голосування!")
        return
    # Telegram Poll обмежує до 10 варіантів
    options = [f"{b['title']} ({b['author']})" for b in books[:10]]
    if len(options) < 2:
        await update.message.reply_text("Потрібно щонайменше 2 книги для голосування.")
        return
    message = await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question="Яку книгу читаємо наступною?",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False
    )
    # Зберігаємо id опитування для підрахунку результатів
    context.chat_data['last_poll_id'] = message.poll.id
    context.chat_data['poll_options'] = options

async def poll_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll = update.poll
    poll_id = poll.id
    options = context.chat_data.get('poll_options', [])
    if not options:
        return
    results = [(opt, votes.voter_count) for opt, votes in zip(options, poll.options)]
    results.sort(key=lambda x: x[1], reverse=True)
    summary = "Підсумки голосування:\n"
    for idx, (opt, count) in enumerate(results, 1):
        summary += f"{idx}. {opt} — {count} голосів\n"
    # Надсилаємо підсумок у групу
    for chat_id in context.bot_data.get('poll_chats', []):
        await context.bot.send_message(chat_id=chat_id, text=summary)

async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Зберігаємо chat_id для надсилання результатів
    chat_id = update.effective_chat.id
    if 'poll_chats' not in context.bot_data:
        context.bot_data['poll_chats'] = set()
    context.bot_data['poll_chats'].add(chat_id)

async def monthly_poll(context: ContextTypes.DEFAULT_TYPE):
    books = load_books()
    if not books:
        return
    options = [f"{b['title']} ({b['author']})" for b in books[:10]]
    if len(options) < 2:
        return
    chat_id = context.job.chat_id
    message = await context.bot.send_poll(
        chat_id=chat_id,
        question="Яку книгу читаємо наступною?",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False
    )
    context.chat_data['last_poll_id'] = message.poll.id
    context.chat_data['poll_options'] = options

async def set_monthly_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Запускаємо щомісячне опитування (наприклад, 1-го числа кожного місяця о 10:00)
    job_queue = context.application.job_queue
    # Видаляємо попередні job для цього чату
    job_queue.get_jobs_by_name(f"monthly_poll_{chat_id}")
    job_queue.run_monthly(
        monthly_poll,
        time=datetime.now().replace(day=1, hour=10, minute=0, second=0, microsecond=0),
        chat_id=chat_id,
        name=f"monthly_poll_{chat_id}"
    )
    await update.message.reply_text("Щомісячне опитування налаштовано!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('addbook', addbook))
    app.add_handler(CommandHandler('listbooks', listbooks))
    app.add_handler(CommandHandler('poll', poll))
    app.add_handler(PollHandler(poll_results))
    app.add_handler(CommandHandler('setmonthlypoll', set_monthly_poll))
    app.run_polling()
    # Запуск JobQueue
    app.job_queue.run_once(lambda ctx: None, 0)  # Ініціалізація JobQueue
