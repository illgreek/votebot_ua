# Telegram Book Club Bot (Vercel + Node.js + MongoDB Atlas)

## Деплой на Vercel

1. Залийте цей репозиторій на GitHub.
2. Підключіть репозиторій до [vercel.com](https://vercel.com/).
3. Додайте змінні оточення:
   - `TELEGRAM_TOKEN` — токен вашого Telegram-бота
   - `MONGODB_URI` — connection string з MongoDB Atlas
   - `CRON_SECRET` — будь-який секретний рядок для захисту cron endpoint
4. Деплойте проект.

## Налаштування webhook у Telegram

Після деплою у вас буде URL типу:
```
https://your-vercel-project.vercel.app/api/index.js
```

Зареєструйте webhook для бота:
```
curl -F "url=https://your-vercel-project.vercel.app/api/index.js" https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook
```

або через браузер:
```
https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-vercel-project.vercel.app/api/index.js
```

## Доступні команди
- `/start` — інструкція
- `/addbook Автор, Назва, Жанр` — додати книгу
- `/listbooks` — список книг
- `/poll` — створити голосування вручну

## Автоматичне опитування через cron-job.org

1. Створіть cron job на [cron-job.org](https://cron-job.org/):
   - URL: `https://your-vercel-project.vercel.app/api/index.js?cron=1&secret=ВАШ_СЕКРЕТ&chat_id=ВАШ_CHAT_ID`
   - Метод: GET
   - Розклад: раз на місяць (наприклад, 1-го числа о 10:00)
2. Готово! Тепер бот автоматично створюватиме опитування у вашій групі.

> ⚠️ Ваш chat_id можна отримати, додавши бота у групу і подивившись update.effective_chat.id через логування або /listbooks.
