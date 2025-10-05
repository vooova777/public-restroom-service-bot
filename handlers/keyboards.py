from telegram import ReplyKeyboardMarkup

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🔍 Знайти поруч", "➕ Додати"],
            ["🚪 Вийти", "🚻 Існуючі вбиральні"],
        ],
        resize_keyboard=True
    )

def get_welcome_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🚪 Увійти", "📝 Реєстрація"]
        ],
        resize_keyboard=True
    )