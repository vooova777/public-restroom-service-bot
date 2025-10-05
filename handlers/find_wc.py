import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters
from db.users import get_token
from config import API_URL
from handlers.keyboards import get_main_keyboard

SEARCH_LOCATION, SEARCH_RANGE = range(100, 102)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True)

async def cancel_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Пошук скасовано.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def find_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Надішліть свою геолокацію (кнопка нижче):",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Надіслати геолокацію", request_location=True)], ["❌ Скасувати"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return SEARCH_LOCATION

async def find_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_find(update, context)
    if update.message.location:
        context.user_data['search_lat'] = update.message.location.latitude
        context.user_data['search_lng'] = update.message.location.longitude
        await update.message.reply_text(
            "Вкажіть радіус пошуку в метрах (наприклад, 500):",
            reply_markup=get_cancel_keyboard()
        )
        return SEARCH_RANGE
    await update.message.reply_text("Будь ласка, надішліть геолокацію кнопкою.")
    return SEARCH_LOCATION

async def find_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel_find(update, context)
    try:
        radius = float(update.message.text)
    except Exception:
        await update.message.reply_text("Введіть число (радіус у метрах):")
        return SEARCH_RANGE

    user_lat = context.user_data.get('search_lat')
    user_lng = context.user_data.get('search_lng')
    if user_lat is None or user_lng is None:
        await update.message.reply_text("Помилка: не вдалося визначити вашу локацію. Почніть спочатку.")
        return ConversationHandler.END

    token = get_token(update.effective_user.id)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    params = {
        "latitude": user_lat,
        "longitude": user_lng,
        "range": radius
    }
    try:
        resp = requests.get(f"{API_URL}/water-closet/get-all-within-range", params=params, headers=headers)
        if resp.ok:
            items = resp.json()
            if not items:
                await update.message.reply_text("Нічого не знайдено в цьому радіусі.", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text(f"Знайдено туалетів: {len(items)}", reply_markup=get_main_keyboard())
                for wc in items:
                    loc = wc.get("location", {})
                    lat = loc.get("latitude")
                    lng = loc.get("longitude")
                    name = wc.get('name', 'Без назви')
                    desc = wc.get('description', '')
                    # Надіслати геолокацію
                    await update.message.reply_location(latitude=lat, longitude=lng)
                    # Лише посилання на Google Maps (від користувача до туалету)
                    gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={user_lat},{user_lng}&destination={lat},{lng}"
                    await update.message.reply_text(
                        f"{name}\n{desc}\n"
                        f"Координати: {lat}, {lng}\n"
                        f"[Маршрут у Google Maps]({gmaps_url})",
                        parse_mode="Markdown",
                    )
        else:
            await update.message.reply_text(f"Помилка пошуку: {resp.status_code}\n{resp.text}", reply_markup=get_main_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Помилка з'єднання: {e}", reply_markup=get_main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

def register(app):
    find_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Знайти поруч$"), find_start)],
        states={
            SEARCH_LOCATION: [
                MessageHandler(filters.LOCATION, find_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, find_location)
            ],
            SEARCH_RANGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_range)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Скасувати$"), cancel_find)],
    )
    app.add_handler(find_conv)