import osimport requests
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Apply nest_asyncio to prevent event loop issues
nest_asyncio.apply()

# Telegram bot token
TOKEN = "7250807380:AAE-dlbFTQUJy7BQfW_TTnUnZXAXlq8bE7U"

# API URL
API_URL = "https://ytvideownloader.ytansh038.workers.dev/?url={}"  # Replace with your actual API URL

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me a YouTube video link to download.")

async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    downloading_msg = await update.message.reply_text("Downloading... Please wait.")
    response = requests.get(API_URL.format(url))
    
    if response.status_code == 200:
        data = response.json()
        
        if not data.get("error", True):
            video_url = data.get("video_with_audio", [{}])[0].get("url", "")
            
            if video_url:
                await update.message.reply_video(video_url)
                await context.bot.delete_message(chat_id=update.message.chat_id, message_id=downloading_msg.message_id)


def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    app.run_polling()

if name == "__main__":
    main()

