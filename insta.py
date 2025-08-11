# bot.py — minimal memory-friendly Telegram voice chat music bot
import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import AudioPiped
import yt_dlp
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("27479878"))
API_HASH = os.getenv("05f8dc8265d4c5df6376dded1d71c0ff")
BOT_TOKEN = os.getenv("8171830754:AAFHMKLVn5XjRM-Sm11vm5q9VJ37iyBMeaA")
SESSION = os.getenv("BQFwyZ4AgNLukhjGMa9vwENy7h2wnm1H6kBF1EC7GMd0k50WaunkgO9JnCBJzjpOhguIkYcyyQYLwILR2KyQbGt-kG9Y9M5zLz2uKp3bgu7zMhyeyNOVvcKps76X7mCU969fwdAHdAabUWOG2a1V4c4GiyMezbKLGUXl7mP3A488MOPT2M3fgp5AhaMD9db7Ww0rjTd-HS0TKb47mr4bFWi58b-Ok5aIzZmfV5t6Rk6YNKUZE_UD-QH_-rU4HNTWkj4i5J5Hg2pkIOR-2__wpz-ID7V_J7h34XxQ9NywiuAwY2VP7VzOlavxWWdP12wq-eyyceqcVQtmBgFjT0ny0DZd7o4y9wAAAAHT5z0DAA")  # userbot session string (required by pytgcalls)

# Safety checks
if not (API_ID and API_HASH and (BOT_TOKEN or SESSION)):
    raise SystemExit("Set API_ID, API_HASH and BOT_TOKEN or SESSION in environment")

# Pyrogram clients
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN) if BOT_TOKEN else None
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION) if SESSION else None

# choose client used by pytgcalls (user account recommended)
caller_client = user if user else bot
call = PyTgCalls(caller_client)

queues = {}  # {chat_id: [(stream_url, title), ...]}
INACTIVE_LEAVE_SECONDS = int(os.getenv("INACTIVE_LEAVE", 300))  # leave after inactivity

# yt-dlp helper (stream URL, title)
YDL_OPTS = {
    "format": "bestaudio[ext=webm][abr<=128]/bestaudio[abr<=128]",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
}

def get_stream(query_or_url: str):
    # supports "ytsearch1:query" and direct urls
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(query_or_url, download=False)
        if "entries" in info:
            info = info["entries"][0]
        url = info.get("url")
        title = info.get("title") or "Unknown Title"
        return url, title


@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply("Hi — minimal music bot. Add me to a group and promote the user session to admin with invite/voice permissions.")


@bot.on_message(filters.command("play") & filters.group)
async def play_cmd(c, m):
    chat_id = m.chat.id
    if len(m.command) < 2:
        return await m.reply("Usage: /play <song name or YouTube link>")
    query = " ".join(m.command[1:])
    await m.reply("🔎 Searching...", quote=True)
    link = query if query.startswith("http") else f"ytsearch1:{query}"
    try:
        stream_url, title = await asyncio.get_event_loop().run_in_executor(None, get_stream, link)
    except Exception as e:
        return await m.reply(f"❌ Error fetching audio: {e}")

    if chat_id not in queues:
        queues[chat_id] = []
    queues[chat_id].append((stream_url, title))

    # if only one track, start playing
    if len(queues[chat_id]) == 1:
        try:
            await call.join_group_call(chat_id, AudioPiped(stream_url))
            await m.reply(f"▶️ Playing: {title}")
        except Exception as e:
            queues.pop(chat_id, None)
            await m.reply(f"❌ Could not join voice chat: {e}")
    else:
        await m.reply(f"➕ Added to queue: {title} (position {len(queues[chat_id])})")


@bot.on_message(filters.command("skip") & filters.group)
async def skip_cmd(c, m):
    chat_id = m.chat.id
    q = queues.get(chat_id)
    if not q or len(q) <= 1:
        return await m.reply("❌ No next track to skip to.")
    # remove current
    q.pop(0)
    next_url, next_title = q[0]
    await call.change_stream(chat_id, AudioPiped(next_url))
    await m.reply(f"⏭ Now playing: {next_title}")


@bot.on_message(filters.command(["pause"]) & filters.group)
async def pause_cmd(c, m):
    await call.pause_stream(m.chat.id)
    await m.reply("⏸ Paused.")


@bot.on_message(filters.command(["resume"]) & filters.group)
async def resume_cmd(c, m):
    await call.resume_stream(m.chat.id)
    await m.reply("▶️ Resumed.")


@call.on_stream_end()
async def _on_stream_end(client, update):
    chat_id = update.chat_id
    q = queues.get(chat_id)
    if q and len(q) > 1:
        q.pop(0)
        next_url, _ = q[0]
        await call.change_stream(chat_id, AudioPiped(next_url))
    else:
        queues.pop(chat_id, None)
        # leave gracefully
        try:
            await call.leave_group_call(chat_id)
        except Exception:
            pass


async def idle_task():
    # keep process alive; pytgcalls has internal idle but we ensure bot stays responsive
    while True:
        await asyncio.sleep(60)


async def main():
    # start whichever clients are available
    if bot:
        await bot.start()
    if user:
        await user.start()

    await call.start()
    print("Bot started")

    # run idle loop and Pyrogram idle
    try:
        await idle()
    finally:
        await call.stop()
        if bot:
            await bot.stop()
        if user:
            await user.stop()


if __name__ == "__main__":
    asyncio.run(main())
