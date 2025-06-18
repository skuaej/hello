import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline

# Logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Load AI Model (Stable Diffusion or any other model for Ghibli-style)
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "stablediffusionapi/ghibli-art"
pipeline = StableDiffusionPipeline.from_pretrained(model_id).to(device)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me a photo and I'll transform it into Ghibli-style art!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_file = await update.message.photo[-1].get_file()
    photo_path = "input.jpg"
    await photo_file.download_to_drive(photo_path)
    
    # Load and process the image
    input_image = Image.open(photo_path)
    prompt = "Convert this image into Ghibli-style art"
    output_image = pipeline(prompt, image=input_image).images[0]
    output_path = "output.jpg"
    output_image.save(output_path)
    
    await update.message.reply_photo(photo=open(output_path, 'rb'))

#YOUR BOT TOKEN 
async def main():
    TOKEN = "7803850244:AAGQCXHd0R7ucXC2chqhQ4xVLKuO8YE6GzY"
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    await application.start_polling()
    await application.idle()

if name == "main":
    import asyncio
    asyncio.run(main())
