import replicate
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# Set your API keys
REPLICATE_API_TOKEN = "r8_Sw4KDHsAwqnm5L6nXZ5fkXal0RrLI8E1g4XPc"
BOT_TOKEN = "7803850244:AAGQCXHd0R7ucXC2chqhQ4xVLKuO8YE6GzY"

# Replicate setup
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌸 Welcome to the Ghibli Image Bot! Use /ghibli <your scene> to get a Ghibli-style image.")

# Ghibli image generation
async def ghibli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Please provide a prompt. Example:\n/ghibli A girl flying on a broom over the ocean")
        return

    await update.message.reply_text("✨ Generating your Ghibli-style image, please wait...")

    # Call Replicate API with a Ghibli-style model
    output = replicate.run(
        "fofr/anything-v4.5:37a3a4a1d683e2c327f4f02a0efdb24a924f3021898cf9473d99473163f9cf78",
        input={
            "prompt": f"{prompt}, Studio Ghibli style, anime illustration, 4k",
            "width": 512,
            "height": 512
        }
    )

    image_url = output[0] if isinstance(output, list) else output
    await update.message.reply_photo(photo=image_url, caption="Here is your Ghibli-style creation! 🌟")

# Run bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ghibli", ghibli))
    print("Bot is running...")
    await app.run_polling()

if name == "main":
    import asyncio
    asyncio.run(main())
