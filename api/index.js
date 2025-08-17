const { Telegraf } = require('telegraf');
const { MongoClient } = require('mongodb');

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);
const mongoUri = process.env.MONGODB_URI;
const cronSecret = process.env.CRON_SECRET;

let db, books;

async function connectDB() {
  if (!db) {
    const client = new MongoClient(mongoUri);
    await client.connect();
    db = client.db();
    books = db.collection('books');
  }
}

bot.start(async (ctx) => {
  await ctx.reply(
    'Вітаю у книжному клубі!\n\n' +
    'Ось доступні команди:\n' +
    '/addbook Автор, Назва, Жанр — додати книгу\n' +
    '/listbooks — переглянути список книг\n' +
    '/poll — створити голосування вручну\n' +
    '/start — показати цю інструкцію ще раз'
  );
});

bot.command('addbook', async (ctx) => {
  await connectDB();
  const text = ctx.message.text.replace('/addbook', '').trim();
  const parts = text.split(',').map((s) => s.trim());
  if (parts.length < 3) {
    return ctx.reply('Будь ласка, використовуйте формат: /addbook Автор, Назва, Жанр');
  }
  const [author, title, genre] = parts;
  await books.insertOne({ author, title, genre, user: ctx.from.first_name });
  ctx.reply(`Книга "${title}" додана до списку!`);
});

bot.command('listbooks', async (ctx) => {
  await connectDB();
  const allBooks = await books.find().toArray();
  if (!allBooks.length) {
    return ctx.reply('Список книг порожній. Додайте першу книгу за допомогою /addbook!');
  }
  let msg = 'Список запропонованих книг:\n';
  allBooks.forEach((b, i) => {
    msg += `${i + 1}. ${b.author} — '${b.title}' [${b.genre}] (від ${b.user})\n`;
  });
  ctx.reply(msg);
});

bot.command('poll', async (ctx) => {
  await connectDB();
  const allBooks = await books.find().toArray();
  if (allBooks.length < 2) {
    return ctx.reply('Потрібно щонайменше 2 книги для голосування.');
  }
  const options = allBooks.slice(0, 10).map((b) => `${b.title} (${b.author})`);
  await ctx.telegram.sendPoll(ctx.chat.id, 'Яку книгу читаємо наступною?', options, {
    is_anonymous: false,
    allows_multiple_answers: false,
  });
});

// Vercel handler
module.exports = async (req, res) => {
  if (req.method === 'POST') {
    // Webhook від Telegram
    try {
      await bot.handleUpdate(req.body);
      res.status(200).send('ok');
    } catch (e) {
      res.status(500).send('bot error');
    }
  } else if (req.method === 'GET' && req.query.cron === '1') {
    // Cron endpoint: /api/index.js?cron=1&secret=...&chat_id=...
    if (req.query.secret !== cronSecret) {
      return res.status(403).send('Forbidden');
    }
    const chatId = req.query.chat_id;
    if (!chatId) {
      return res.status(400).send('No chat_id');
    }
    await connectDB();
    const allBooks = await books.find().toArray();
    if (allBooks.length < 2) {
      return res.status(200).send('not enough books');
    }
    const options = allBooks.slice(0, 10).map((b) => `${b.title} (${b.author})`);
    await bot.telegram.sendPoll(chatId, 'Яку книгу читаємо наступною?', options, {
      is_anonymous: false,
      allows_multiple_answers: false,
    });
    res.status(200).send('poll sent');
  } else {
    res.status(405).send('Method Not Allowed');
  }
};
