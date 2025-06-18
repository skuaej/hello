import os
import replicate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from io import BytesIO

# Set your API tokens (preferably use environment variables)
REPLICATE_API_TOKEN = "r8_Sw4KDHsAwqnm5L6nXZ5fkXal0RrLI8E1g4XPc"
TELEGRAM_BOT_TOKEN = "7803850244:AAGQCXHd0R7ucXC2chqhQ4xVLKuO8YE6GzY"

# Initialize Replicate client
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# Function to generate Ghibli-style image using Replicate
def generate_ghibli_image(prompt):
    # Use Flux.1 model for high-quality Ghibli-style generation
    model = "black-forest-labs/flux.1-dev"
    input = {
        "prompt": f"{prompt}, in the style of Studio Ghibli, whimsical, soft colors, detailed landscapes, hand-drawn aesthetic",
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "png",
        "output_quality": 80
    }
    try:
        output = client.run(model, input=input)
        return output[0]  # Returns the URL of the generated image
    except Exception as e:
        return f"Error generating image: {str(e)}"

# Telegram bot command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Ghibli Art Bot! Send a description (e.g., 'A serene forest with a Totoro-like creature') to generate a Studio Ghibli-style image."
    )

# Telegram bot message handler for text prompts
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    await update.message.reply_text("Generating your Ghibli-style image, please wait...")

    # Generate image
    image_url = generate_ghibli_image(user_prompt)
    
    if isinstance(image_url, str) and image_url.startswith("http"):
        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            image = BytesIO(response.content)
            await update.message.reply_photo(photo=image, caption="Your Ghibli-style art!")
        else:
            await update.message.reply_text("Failed to retrieve the generated image.")
    else:
        await update.message.reply_text(image_url)  # Error message

# Main function to run the bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == "main":
    main()
