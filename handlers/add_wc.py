import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters
from db.users import get_token
from config import API_URL
from handlers.keyboards import get_main_keyboard, get_welcome_keyboard

WC_NAME, WC_DESCRIPTION, WC_ISFREE, WC_FEATURES, WC_LOCATION, WC_PHOTO, WC_CONFIRM = range(7)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Додавання скасовано.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    token = get_token(user_id)
    if not token:
        await update.message.reply_text(
            "Щоб додати вбиральню, увійдіть або зареєструйтесь.",
            reply_markup=get_welcome_keyboard()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "Введіть назву вбиральні:",
        reply_markup=get_cancel_keyboard()
    )
    return WC_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    context.user_data['wc_name'] = update.message.text
    await update.message.reply_text(
        "Введіть опис:",
        reply_markup=get_cancel_keyboard()
    )
    return WC_DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    context.user_data['wc_description'] = update.message.text
    await update.message.reply_text(
        "Вбиральня безкоштовна?",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ Так", "❌ Ні"], ["❌ Скасувати"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return WC_ISFREE

async def add_isfree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    text = update.message.text.strip()
    if text == "✅ Так":
        context.user_data['wc_isfree'] = True
    elif text == "❌ Ні":
        context.user_data['wc_isfree'] = False
    else:
        await update.message.reply_text("Будь ласка, оберіть варіант кнопкою.", reply_markup=ReplyKeyboardMarkup(
            [["✅ Так", "❌ Ні"], ["❌ Скасувати"]],
            resize_keyboard=True, one_time_keyboard=True))
        return WC_ISFREE
    await update.message.reply_text(
        "Вкажіть особливості доступності (через кому), або натисніть \"Пропустити\":",
        reply_markup=ReplyKeyboardMarkup([["Пропустити"], ["❌ Скасувати"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return WC_FEATURES

async def add_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    if update.message.text == "Пропустити":
        context.user_data['wc_features'] = {}
    else:
        features = [s.strip() for s in update.message.text.split(",") if s.strip()]
        context.user_data['wc_features'] = {
            f"feature{i+1}": feat for i, feat in enumerate(features)
        }
    await update.message.reply_text(
        "📍 Надішліть геолокацію вбиральні (кнопкою нижче):",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Надіслати геолокацію", request_location=True)], ["❌ Скасувати"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return WC_LOCATION

async def add_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    if update.message.location:
        lat = update.message.location.latitude
        lng = update.message.location.longitude
        context.user_data['wc_lat'] = lat
        context.user_data['wc_lng'] = lng
    else:
        await update.message.reply_text("Будь ласка, надішліть геолокацію кнопкою.")
        return WC_LOCATION
    await update.message.reply_text(
        "📸 Надішліть фото вбиральні (обов'язково):",
        reply_markup=get_cancel_keyboard()
    )
    return WC_PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    if not update.message.photo:
        await update.message.reply_text("Будь ласка, надішліть саме фото вбиральні.")
        return WC_PHOTO

    user_id = update.effective_user.id
    token = get_token(user_id)
    field_name = 'image'

    file = await update.message.photo[-1].get_file()
    file_bytes = await file.download_as_bytearray()
    files = {field_name: ('photo.jpg', file_bytes, 'image/jpeg')}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.post(f"{API_URL}/photo", files=files, headers=headers)
        if not resp.ok:
            await update.message.reply_text(
                f"Помилка завантаження фото: {resp.status_code}\n"
                f"Тіло відповіді:\n{resp.text}\n"
                f"Raw content:\n{resp.content}"
            )
            return WC_PHOTO
        photo_resp = resp.json()
        photo_uuid = photo_resp.get("draftPhotoId")
        if not photo_uuid:
            await update.message.reply_text(f"Помилка: не вдалося отримати UUID фото.\nДоступні ключі: {list(photo_resp.keys())}")
            return WC_PHOTO
        context.user_data['wc_photo_uuid'] = photo_uuid

    except Exception as e:
        await update.message.reply_text(f"Помилка завантаження фото: {e}")
        return WC_PHOTO

    preview = (
        f"Перевірте дані:\n"
        f"Назва: {context.user_data['wc_name']}\n"
        f"Опис: {context.user_data['wc_description']}\n"
        f"Безкоштовний: {'так' if context.user_data['wc_isfree'] else 'ні'}\n"
        f"Особливості: "
        f"{', '.join(context.user_data['wc_features'].values()) if context.user_data['wc_features'] else 'немає'}\n"
        f"Координати: {context.user_data['wc_lat']}, {context.user_data['wc_lng']}\n"
        f"Фото: додано\n\n"
        f"Все вірно? (✅ Так / ❌ Ні)"
    )
    await update.message.reply_text(
        preview,
        reply_markup=ReplyKeyboardMarkup([["✅ Так", "❌ Ні"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return WC_CONFIRM

async def add_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Скасувати":
        return await cancel(update, context)
    if update.message.text != "✅ Так":
        context.user_data.clear()
        await update.message.reply_text(
            "Додавання скасовано.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    user_id = update.effective_user.id
    token = get_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        "name": context.user_data['wc_name'],
        "description": context.user_data['wc_description'],
        "isFree": context.user_data['wc_isfree'],
        "accessibilityFeatures": context.user_data['wc_features'],
        "location": {
            "latitude": context.user_data['wc_lat'],
            "longitude": context.user_data['wc_lng']
        },
        "draftPhotoUuids": [context.user_data['wc_photo_uuid']]
    }

    try:
        resp = requests.post(f"{API_URL}/water-closet", json=data, headers=headers)
        if resp.ok:
            await update.message.reply_text("Вбиральню успішно додано! Дякуємо.", reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(f"Помилка додавання: {resp.status_code} {resp.text}", reply_markup=get_main_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Помилка з'єднання: {e}", reply_markup=get_main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

def register(app):
    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Додати$"), add_start)],
        states={
            WC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            WC_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            WC_ISFREE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_isfree)],
            WC_FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_features)],
            WC_LOCATION: [
                MessageHandler(filters.LOCATION, add_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_location)
            ],
            WC_PHOTO: [MessageHandler(filters.PHOTO, add_photo), MessageHandler(filters.TEXT & ~filters.COMMAND, add_photo)],
            WC_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_confirm)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Скасувати$"), cancel)]
    )
    app.add_handler(add_conv)