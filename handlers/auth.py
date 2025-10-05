import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters
from db.users import set_token, clear_token, get_token
from config import API_URL
from handlers.keyboards import get_main_keyboard, get_welcome_keyboard

LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
REGISTER_USERNAME, REGISTER_EMAIL, REGISTER_FIRSTNAME, REGISTER_LASTNAME, REGISTER_PASSWORD = range(2, 7)

async def cancel_login_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Дію скасовано.", reply_markup=get_welcome_keyboard())
    return ConversationHandler.END

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введіть ваш username:",
        reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return LOGIN_USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    context.user_data['login_username'] = update.message.text
    await update.message.reply_text("Введіть пароль:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    username = context.user_data['login_username']
    password = update.message.text
    try:
        resp = requests.post(f"{API_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        if resp.status_code in (200, 201):
            data = resp.json()
            print("LOGIN RESPONSE:", data)
            token = data.get("accessToken") or data.get("token") or data.get("jwt") or data.get("access_token")
            set_token(update.effective_user.id, update.effective_user.username, token)
            if token:
                await update.message.reply_text("Успішний вхід! Ось ваші опції:", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text("Помилка: токен не отримано. Перевірте дані.", reply_markup=get_welcome_keyboard())
        else:
            await update.message.reply_text(f"Помилка авторизації: {resp.status_code} {resp.text}", reply_markup=get_welcome_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Помилка з'єднання: {e}", reply_markup=get_welcome_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

async def handle_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть username для реєстрації:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
    return REGISTER_USERNAME

async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    context.user_data['register_username'] = update.message.text
    await update.message.reply_text("Введіть email:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    context.user_data['register_email'] = update.message.text
    await update.message.reply_text("Введіть ваше ім'я:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
    return REGISTER_FIRSTNAME

async def register_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    context.user_data['register_firstname'] = update.message.text
    await update.message.reply_text("Введіть ваше прізвище:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
    return REGISTER_LASTNAME

async def register_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    context.user_data['register_lastname'] = update.message.text
    await update.message.reply_text("Введіть пароль:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_login_register(update, context)
    username = context.user_data['register_username']
    email = context.user_data['register_email']
    first_name = context.user_data['register_firstname']
    last_name = context.user_data['register_lastname']
    password = update.message.text
    try:
        resp = requests.post(f"{API_URL}/auth/register", json={
            "username": username,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "password": password
        })
        if resp.status_code in (200, 201):
            data = resp.json()
            print("REGISTER RESPONSE:", data)  # для відладки
            await update.message.reply_text("Реєстрація пройшла успішно. Тепер увійдіть!", reply_markup=get_welcome_keyboard())
        else:
            await update.message.reply_text(f"Помилка реєстрації: {resp.status_code} {resp.text}", reply_markup=get_welcome_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Помилка з'єднання: {e}", reply_markup=get_welcome_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_token(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text("Ви вийшли з акаунта.", reply_markup=get_welcome_keyboard())

def register(app):
    login_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚪 Увійти$"), handle_login)],
        states={
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Скасувати$"), cancel_login_register)]
    )
    register_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Реєстрація$"), handle_register)],
        states={
            REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_firstname)],
            REGISTER_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_lastname)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Скасувати$"), cancel_login_register)]
    )
    app.add_handler(login_conv)
    app.add_handler(register_conv)
    app.add_handler(MessageHandler(filters.Regex("^🚪 Вийти$"), logout))