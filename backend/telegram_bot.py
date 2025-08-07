import os
import telegram
print(f"✅ python-telegram-bot version: {telegram.__version__}")

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["CuteStarsDB"]
applications = db["applications"]

LANGUAGE, EMAIL = range(2)
LANGUAGES = ["English", "Spanish", "Portuguese", "Russian", "Serbian"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    context.user_data["telegram_id"] = telegram_id

    reply_markup = ReplyKeyboardMarkup(
        [[lang] for lang in LANGUAGES],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "👋 Welcome! Please choose your preferred language:",
        reply_markup=reply_markup
    )
    return LANGUAGE

async def receive_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = update.message.text
    context.user_data["language"] = language

    await update.message.reply_text("📧 Please enter your email (the same one you used to apply):")
    return EMAIL

async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    telegram_id = context.user_data["telegram_id"]
    language = context.user_data["language"]

    applicant = applications.find_one({"email": email})
    if not applicant:
        await update.message.reply_text("❌ No application found with this email. Please double-check and try again.")
        return ConversationHandler.END

    applications.update_one(
        {"_id": applicant["_id"]},
        {"$set": {
            "telegram_id": telegram_id,
            "language": language
        }}
    )
    await update.message.reply_text("✅ Verified! Please wait while we guide you to the next steps.")
    return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Please follow the instructions shown by the bot.")

def run_bot():
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_language)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        },
        fallbacks=[MessageHandler(filters.ALL, fallback)],
    )

    application.add_handler(conv_handler)
    print("✅ Telegram bot is running...")
    application.run_polling()

if __name__ == "__main__":
    run_bot()
