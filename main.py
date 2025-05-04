import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

#created by @cyber_ansh on telegram 
BOT_TOKEN = "7250807380:AAE-dlbFTQUJy7BQfW_TTnUnZXAXlq8bE7U"
API_URL = "https://instadownload.ytansh038.workers.dev/?url="

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(name)

async def start(update: Update, context: CallbackContext) -> None:
    buttons = [
        [InlineKeyboardButton("👨‍💻 Owner", url="t.me/cyber_ansh")],
        [InlineKeyboardButton("🔹 Support", url="https://t.me/cyber_ansh")],
        [InlineKeyboardButton("🔸 Group", url="https://t.me/+7AUuVrP8F69kYWY1")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await update.message.reply_text(
        "Welcome! Send me an Instagram Reel/Video link and I will download it for you.",
        reply_markup=reply_markup
    )

async def download_instagram_video(update: Update, context: CallbackContext) -> None:
    message = update.message
    chat_id = message.chat_id
    message_id = message.message_id  # User ka message ID (delete karne ke liye)

    if "instagram.com" not in message.text:
        sent_message = await message.reply_text("❌ Invalid Instagram URL. Please send a valid Instagram Reel or Video link.")
        await sent_message.delete()
        return

    # "Downloading..." message send karo
    progress_message = await message.reply_text("🔄 Downloading your video, please wait...")

    try:
        response = requests.get(API_URL + message.text).json()

        if response.get("error"):
            await message.reply_text("❌ Failed to fetch the video. Please try again later.")
            await progress_message.delete()
            return

        video_url = response["result"]["url"]
        file_size = response["result"]["formattedSize"]

        await message.reply_text(f"✅ Video Found! Size: {file_size}\n⬇ Downloading...")

        # Video send karo
        sent_video = await message.reply_video(video=video_url, caption="Here is your downloaded Instagram video!")

        # FIX 1: Message delete method correctly call karo
         # User ka Instagram link waala message delete karo
        await progress_message.delete()  # "Downloading..." message delete karo
        
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply_text("❌ An error occurred. Please try again later.")
        await progress_message.delete()

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram_video))

    logger.info("Bot is running...")
    app.run_polling()

if name == "main":
    main()
