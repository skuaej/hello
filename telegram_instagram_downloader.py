from telegram.ext import Application, CommandHandler

# Replace 'YOUR_BOT_TOKEN' with the token you got from @BotFather
BOT_TOKEN = '7762247683:AAGFSkwkKVKxFlN1IqPJ7SjvHQhfNyEnpBM'

# Define the start command handler
async def start(update, context):
    await update.message.reply_text('hi')

def main():
    # Create the Application and pass the bot token
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handler for the /start command
    application.add_handler(CommandHandler('start', start))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
