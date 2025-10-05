import os

TOKEN = os.getenv("TELEGRAM_TOKEN")  # токен телеграм-бота
API_URL = os.getenv("API_URL", "http://localhost:8080/api")  # backend API