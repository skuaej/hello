import instaloader
import requests
import os
from io import BytesIO
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import logging
import re

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Telegram Bot Token from environment variable
BOT_TOKEN = os.getenv("7250807380:AAE-dlbFTQUJy7BQfW_TTnUnZXAXlq8bE7U")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

# Initialize Instaloader
ig = instaloader.Instaloader()

# Function to validate Instagram URL
def is_valid_instagram_url(url):
    pattern = r"https?://www\.instagram\.com/(p|reel)/[A-Za-z0-9_-]+/?"
    return re.match(pattern, url)

# Function to download Instagram media
def download_instagram_media(url):
    try:
        # Extract shortcode from URL
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(ig.context, shortcode)
        
        # Download media
        if post.is_video:
            video_url = post.video_url
            response = requests.get(video_url)
            if response.status_code == 200:
                return BytesIO(response.content), "video"
        else:
            image_url = post.url
            response = requests.get(image_url)
            if response.status_code == 200:
                return BytesIO(response.content), "image"
        
        return None, None
    except instaloader.exceptions.TooManyRequestsException:
        logger.error("Rate limit reached.")
        return None, "rate_limit"
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None, None

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm an Instagram Downloader Bot. Send me a public Instagram post or reel URL, and I'll download the media for you!"
    )

# Message handler for Instagram URLs
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if not is_valid_instagram_url(url):
        await update.message.reply_text("Please send a valid Instagram post or reel URL.")
        return
    
    await update.message.reply_text("Processing your request, please wait...")
    
    media, media_type = download_instagram_media(url)
    
    if media and media_type in ["video", "image"]:
        if media_type == "video":
            await update.message.reply_video(video=media, filename="instagram_video.mp4")
        else:
            await update.message.reply_photo(photo=media, filename="instagram_image.jpg")
        await update.message.reply_text("Download successful! Send another URL or use /start to restart.")
    elif media_type == "rate_limit":
        await update.message.reply_text("Rate limit reached. Please try again later or contact the bot admin.")
    else:
        await update.message.reply_text("Failed to download the Instagram content. Ensure the URL is correct and the post is public.")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("An error occurred. Please try again.")

def main():
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
