from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Replace 'YOUR_API_TOKEN' with the actual token you received from BotFather.
API_TOKEN = '8171830754:AAFHMKLVn5XjRM-Sm11vm5q9VJ37iyBMeaA'

# Define the command handler for the /start command.
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a 'Hi!' message when the /start command is issued."""
    await update.message.reply_text('Hi!')


def main() -> None:
    """Starts the bot."""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Register the command handler.
    application.add_handler(CommandHandler("start", start_command))

    # Start the bot, polling for updates.
    application.run_polling(poll_interval=2) # polls every 2 seconds


if __name__ == '__main__':
    main()
