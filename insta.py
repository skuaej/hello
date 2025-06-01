from telegram.ext import Updater, CommandHandler

# Define the function to handle the /start command
def start(update, context):
    update.message.reply_text('hi')

def main():
    # Replace 'YOUR_BOT_TOKEN' with the token from BotFather
    updater = Updater("7223902701:AAGjFpY6qrmVaJJpUwGPdvBLZHrzQCd3UvQ", use_context=True)
    dp = updater.dispatcher

    # Add a handler for the /start command
    dp.add_handler(CommandHandler("start", start))

    # Start the bot
    updater.start_polling()
    updater.idle()

if name == 'main':
    main()
