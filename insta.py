mimport os
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.environ.get("8171830754:AAFHMKLVn5XjRM-Sm11vm5q9VJ37iyBMeaA")

if not BOT_TOKEN:
    raise RuntimeError("Please set TELEGRAM_BOT_TOKEN environment variable.")

def start(update, context):
    update.message.reply_text("Hi")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
