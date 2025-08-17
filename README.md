# Telegram Book Club Bot (Vercel Webhook)

## Як задеплоїти на Vercel

1. **Залийте цей репозиторій на GitHub.**
2. **Зареєструйтеся на [vercel.com](https://vercel.com/) та підключіть репозиторій.**
3. **Вкажіть змінну оточення TELEGRAM_TOKEN** (у Vercel Dashboard → Project Settings → Environment Variables):
   - `TELEGRAM_TOKEN=ваш_токен_бота`
4. **Деплойте проект.**

## Налаштування webhook у Telegram

Після деплою у вас буде URL типу:
```
https://your-vercel-project.vercel.app/api
```

Зареєструйте webhook для бота (замініть `TOKEN` і `URL`):

```
curl -F "url=https://your-vercel-project.vercel.app/api" https://api.telegram.org/botTOKEN/setWebhook
```

або через браузер:
```
https://api.telegram.org/botTOKEN/setWebhook?url=https://your-vercel-project.vercel.app/api
```

## Доступні команди
- `/start` — інструкція
- `/addbook Автор, Назва, Жанр` — додати книгу
- `/listbooks` — список книг
- `/poll` — створити голосування вручну

> ⚠️ Автоматичне щомісячне опитування на Vercel не працює (немає фонових задач)

## Автоматичне щомісячне опитування через cron-job.org

1. Додайте у Vercel змінні оточення:
   - `CRON_SECRET=ваш_секрет` (будь-який складний рядок)
2. Перейдіть на [cron-job.org](https://cron-job.org/) і створіть новий cron job:
   - URL: `https://your-vercel-project.vercel.app/api/cron?secret=ваш_секрет&chat_id=ВАШ_CHAT_ID`
   - Метод: POST
   - Розклад: раз на місяць (наприклад, 1-го числа о 10:00)
3. Готово! Тепер бот автоматично створюватиме опитування у вашій групі.

> ⚠️ Ваш chat_id можна отримати, додавши бота у групу і написавши йому, а потім подивитися update через getUpdates або тимчасово додати логування update.effective_chat.id у коді.
