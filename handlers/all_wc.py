import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters
from db.users import get_token
from config import API_URL
from handlers.keyboards import get_main_keyboard

CENTER_LAT = 0
CENTER_LNG = 0
BIG_RADIUS = 20000000  # 20 000 км

(
    FILTER_START,
    FILTER_FREE,
    FILTER_KEYWORD
) = range(3)

def get_filter_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Показати всі", "Тільки безкоштовні"],
            ["Пошук за словом", "❌ Скасувати"]
        ],
        resize_keyboard=True
    )

async def cancel_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Перегляд скасовано.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def filter_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оберіть фільтр для перегляду туалетів:",
        reply_markup=get_filter_keyboard()
    )
    return FILTER_START

async def filter_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Скасувати":
        return await cancel_filter(update, context)
    elif text == "Показати всі":
        context.user_data['filter'] = {"mode": "all"}
        return await show_wc_list(update, context)
    elif text == "Тільки безкоштовні":
        context.user_data['filter'] = {"mode": "free"}
        return await show_wc_list(update, context)
    elif text == "Пошук за словом":
        await update.message.reply_text("Введіть слово для пошуку за назвою або описом:", reply_markup=ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True))
        return FILTER_KEYWORD
    else:
        await update.message.reply_text("Оберіть дію через кнопки.", reply_markup=get_filter_keyboard())
        return FILTER_START

async def filter_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Скасувати":
        return await cancel_filter(update, context)
    context.user_data['filter'] = {"mode": "keyword", "keyword": text.strip().lower()}
    return await show_wc_list(update, context)

async def show_wc_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = get_token(update.effective_user.id)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    params = {
        "latitude": CENTER_LAT,
        "longitude": CENTER_LNG,
        "range": BIG_RADIUS
    }

    filter_mode = context.user_data.get('filter', {}).get("mode", "all")
    keyword = context.user_data.get('filter', {}).get("keyword", "")

    try:
        resp = requests.get(f"{API_URL}/water-closet/get-all-within-range", params=params, headers=headers)
        if resp.ok:
            items = resp.json()
            # Фільтрація на боці бота
            if filter_mode == "free":
                items = [wc for wc in items if wc.get("isFree")]
            elif filter_mode == "keyword":
                items = [
                    wc for wc in items
                    if keyword in (wc.get("name") or "").lower() or keyword in (wc.get("description") or "").lower()
                ]
            if not items:
                await update.message.reply_text("Підходящих туалетів немає.", reply_markup=get_main_keyboard())
                context.user_data.clear()
                return ConversationHandler.END
            for wc in items:
                loc = wc.get("location", {})
                lat = loc.get("latitude")
                lng = loc.get("longitude")
                name = wc.get("name", "Без назви")
                desc = wc.get("description", "")
                is_free = wc.get("isFree", None)
                free_str = "Безкоштовний" if is_free else "Платний" if is_free is not None else ""
                # Надіслати геомітку
                if lat is not None and lng is not None:
                    await update.message.reply_location(latitude=lat, longitude=lng)
                await update.message.reply_text(
                    f"🚻 {name}\n{desc}\n{free_str}\nКоординати: {lat}, {lng}",
                    reply_markup=get_main_keyboard()
                )
        else:
            await update.message.reply_text(
                f"Помилка при завантаженні: {resp.status_code} {resp.text}",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        await update.message.reply_text(f"Помилка з'єднання: {e}", reply_markup=get_main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

def register(app):
    wc_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚻 Існуючі вбиральні$"), filter_start)],
        states={
            FILTER_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, filter_select)],
            FILTER_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, filter_keyword)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Скасувати$"), cancel_filter)],
    )
    app.add_handler(wc_conv)