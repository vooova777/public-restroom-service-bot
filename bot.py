from telegram.ext import Application
from dotenv import load_dotenv
load_dotenv()
from config import TOKEN
from db.users import setup as db_setup

from handlers.start import register as register_start
from handlers.add_wc import register as register_add_wc
from handlers.find_wc import register as register_find_wc
from handlers.auth import register as register_auth
from handlers.all_wc import register as register_all_wc


def main():
    print("Запуск бота...")
    db_setup()  # ініціалізація бази SQLite
    app = Application.builder().token(TOKEN).build()
    register_start(app) 
    register_add_wc(app)
    register_find_wc(app)
    register_auth(app)
    register_all_wc(app)
    app.run_polling()

if __name__ == "__main__":
    main()