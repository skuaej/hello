from pyrogram import Client, filters
import instaloader
import requests
import os
from pyrogram.types import InputMediaPhoto, InputMediaVideo
import re

from TEAMZYRO import app 

L = instaloader.Instaloader()

# Helper function to extract Instagram URL from text
def extract_instagram_url(text):
    # Regex to match Instagram URLs (post or reel)
    pattern = r"(https?://(?:www\.)?instagram\.com/(?:p|reel)/[A-Za-z0-9_-]+/?)"
    match = re.search(pattern, text)
    return match.group(0) if match else None

# Helper function to download media
def download_instagram_media(url):
    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        media_files = []

        if post.typename == 'GraphSidecar':
            for index, node in enumerate(post.get_sidecar_nodes()):
                media_url = node.video_url if node.is_video else node.display_url
                ext = "mp4" if node.is_video else "jpg"
                filename = f"media_{index}.{ext}"

                r = requests.get(media_url)
                with open(filename, "wb") as f:
                    f.write(r.content)
                media_files.append((filename, ext))
        else:
            media_url = post.video_url if post.is_video else post.url
            ext = "mp4" if post.is_video else "jpg"
            filename = f"media.{ext}"
            r = requests.get(media_url)
            with open(filename, "wb") as f:
                f.write(r.content)
            media_files.append((filename, ext))

        return media_files, None

    except Exception as e:
        return None, str(e)

# Handler for messages containing Instagram links (works in groups and DMs)
@app.on_message(filters.text & (filters.private | filters.group))
async def auto_reel_handler(client, message):
    # Extract Instagram URL from the message
    url = extract_instagram_url(message.text)
    if not url:
        return  # Ignore messages without Instagram URLs

    # Send processing message
    processing = await message.reply("⏳ Downloading...")

    # Download media
    media_files, error = download_instagram_media(url)

    if error:
        return await processing.edit(f"❌ Error: {error}")

    # Group media in batches of 4
    group = []
    for i, (filename, ext) in enumerate(media_files):
        if ext == "mp4":
            group.append(InputMediaVideo(open(filename, "rb")))
        else:
            group.append(InputMediaPhoto(open(filename, "rb")))

        # Send batch if 4 items or last group
        if len(group) == 4 or i == len(media_files) - 1:
            try:
                await client.send_media_group(chat_id=message.chat.id, media=group)
            except Exception as e:
                await message.reply(f"⚠️ Failed to send batch: {e}")
            group = []

    # Delete processing message
    await processing.delete()

    # Cleanup
    for filename, _ in media_files:
        if os.path.exists(filename):
            os.remove(filename)
