# PublicRestroomServiceBot

## Запуск через Docker

1. Клонуй репозиторій:

   ```bash
   git clone https://github.com/vooova777/public-restroom-service-bot.git
   cd public-restroom-service-bot
   ```

2. Створи файл `.env` і пропиши змінні:

   ```
   TELEGRAM_TOKEN=твій_токен
   API_URL=http://адреса_твого_бекенду/api
   ```

3. Збери та запусти контейнер:

   ```bash
   docker compose up --build -d
   ```

4. Для перегляду логів:
   ```bash
   docker compose logs -f
   ```

## Оновлення коду

1. Після змін перезапусти контейнер:
   ```bash
   docker compose restart
   ```
