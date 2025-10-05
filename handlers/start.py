from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from handlers.keyboards import get_welcome_keyboard

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю! Це бот-помічник щодо вбиралень вашого міста. Оберіть, будь ласка, бажану дію, натиснувши на одну з кнопок внизу.",
        reply_markup=get_welcome_keyboard()
    )

def register(app):
    app.add_handler(CommandHandler("start", start_handler))