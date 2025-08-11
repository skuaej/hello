#!/usr/bin/env python3
"""
Telegram Terabox downloader bot.

Usage:
  - Set environment variable TELEGRAM_BOT_TOKEN
  - Run: python bot.py
Commands:
  /start      - help message
  /download <terabox_share_url>  - attempt to fetch download link (and optionally upload)
Or simply send the terabox share URL to the bot.
"""

import os
import asyncio
import logging
from urllib.parse import quote_plus

from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
import tempfile
import math

# config
API_PROXY_BASE = "https://terad.rishuapi.workers.dev/?url="  # the proxy API you provided
BOT_TOKEN = os.environ.get("8171830754:AAFHMKLVn5XjRM-Sm11vm5q9VJ37iyBMeaA")  # set this in env
MAX_UPLOAD_BYTES = 40 * 1024 * 1024  # conservative threshold for uploading via bot (40 MB). Adjust as you like.

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_proxy(api_url: str, session: aiohttp.ClientSession):
    """Fetch JSON (or fallback) from the proxy API."""
    async with session.get(api_url, timeout=60) as resp:
        content_type = resp.headers.get("Content-Type", "")
        text = await resp.text()
        # try parse json
        try:
            return await resp.json()
        except Exception:
            # return raw text if not json
            return {"raw_text": text, "content_type": content_type, "status": resp.status}


def extract_download_link(proxy_response):
    """
    Attempt robust extraction of a usable download link from proxy_response.
    The proxy API structures may vary; this function checks common places.
    Returns tuple (download_url, filename or None, filesize_bytes or None)
    """
    if not proxy_response:
        return (None, None, None)

    # If proxy returned dict with obvious fields
    if isinstance(proxy_response, dict):
        keys = proxy_response.keys()
        # common guesses:
        for key in ("download", "url", "link", "file", "download_url"):
            if key in proxy_response and isinstance(proxy_response[key], str):
                return (proxy_response[key], proxy_response.get("name") or proxy_response.get("filename"), proxy_response.get("size"))

        # nested data
        if "data" in proxy_response:
            data = proxy_response["data"]
            if isinstance(data, dict):
                for key in ("download", "url", "link", "file", "download_url"):
                    if key in data and isinstance(data[key], str):
                        return (data[key], data.get("name") or data.get("filename"), data.get("size"))
                # maybe data['files'] is a list
                if "files" in data and isinstance(data["files"], list) and len(data["files"]) > 0:
                    f0 = data["files"][0]
                    if isinstance(f0, dict) and ("url" in f0 or "download" in f0):
                        dl = f0.get("url") or f0.get("download")
                        return (dl, f0.get("name") or f0.get("filename"), f0.get("size"))
        # fallback: maybe proxy returned raw_text in 'raw_text'
        if "raw_text" in proxy_response and isinstance(proxy_response["raw_text"], str):
            raw = proxy_response["raw_text"]
            # find http link inside text (very simple)
            import re
            m = re.search(r"(https?://[^\s'\"<>]+)", raw)
            if m:
                return (m.group(1), None, None)

    # unknown format
    return (None, None, None)


async def try_get_file_info(url: str, session: aiohttp.ClientSession):
    """HEAD request to get content-length and filename suggestion when available."""
    try:
        async with session.head(url, timeout=30) as resp:
            size = resp.headers.get("Content-Length")
            ct = resp.headers.get("Content-Type")
            cd = resp.headers.get("Content-Disposition")
            filename = None
            if cd:
                import re
                m = re.search(r'filename\*?=([^;]+)', cd)
                if m:
                    filename = m.group(1).strip(' "\'')
            size_bytes = int(size) if size and size.isdigit() else None
            return size_bytes, filename, ct
    except Exception:
        return None, None, None


async def download_stream_to_temp(url: str, session: aiohttp.ClientSession, max_bytes=None):
    """
    Stream-download file to a temporary file.
    If max_bytes provided and more data exists than max_bytes, stop and return None (indicates too large).
    Returns tuple (tempfile_path, actual_size_bytes)
    """
    chunk_size = 64 * 1024
    tmp = tempfile.NamedTemporaryFile(delete=False)
    total = 0
    try:
        async with session.get(url, timeout=120) as resp:
            if resp.status != 200:
                tmp.close()
                return None, None
            async for chunk in resp.content.iter_chunked(chunk_size):
                if not chunk:
                    break
                tmp.write(chunk)
                total += len(chunk)
                if max_bytes and total > max_bytes:
                    tmp.close()
                    return None, total
    except Exception as e:
        logger.exception("Error downloading stream: %s", e)
        tmp.close()
        return None, None
    tmp.flush()
    tmp.close()
    return tmp.name, total


async def send_download_link_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE, download_url, filename=None, filesize=None):
    """Decide whether to upload file to Telegram or send the direct link."""
    chat_id = update.effective_chat.id
    # Try to figure file size: prefer provided filesize, else HEAD
    async with aiohttp.ClientSession() as session:
        if not filesize:
            size_head, inferred_name, _ = await try_get_file_info(download_url, session)
            if size_head:
                filesize = size_head
            if not filename:
                filename = inferred_name

    if filesize and filesize <= MAX_UPLOAD_BYTES:
        # try to download and upload
        msg = await update.message.reply_text(f"File size {filesize} bytes — downloading and uploading to Telegram (this may take a while)...")
        async with aiohttp.ClientSession() as session:
            tmp_path, actual = await download_stream_to_temp(download_url, session, max_bytes=MAX_UPLOAD_BYTES+1)
            if tmp_path and actual and actual <= MAX_UPLOAD_BYTES:
                try:
                    with open(tmp_path, "rb") as f:
                        await context.bot.send_document(chat_id=chat_id, document=InputFile(f, filename or os.path.basename(tmp_path)))
                    await msg.edit_text("Uploaded file successfully.")
                except Exception as e:
                    logger.exception("Upload failed")
                    await msg.edit_text("Upload failed — sending direct download link instead.")
                    await context.bot.send_message(chat_id=chat_id, text=f"Download link: {download_url}")
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            else:
                # too large or download error
                await msg.edit_text("File is larger than allowed for upload or download failed. Sending direct download link instead.")
                await context.bot.send_message(chat_id=chat_id, text=f"Download link: {download_url}")
    else:
        # don't upload, just send link
        size_text = f" (~{filesize} bytes)" if filesize else ""
        await update.message.reply_text(f"Direct download link{size_text}:\n{download_url}")


async def handle_download_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /download command or plain messages with terabox url."""
    text = (update.message.text or "").strip()
    if text.startswith("/download"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("Usage: /download <terabox share url>\nOr just send the share URL as a message.")
            return
        share_url = parts[1].strip()
    else:
        share_url = text

    if not share_url or not share_url.startswith("http"):
        await update.message.reply_text("Please send a valid Terabox share URL (starting with http/https) or use /download <url>.")
        return

    msg = await update.message.reply_text("Resolving the share link via proxy API...")
    # build proxy api request
    api_call = API_PROXY_BASE + quote_plus(share_url)
    logger.info("Proxy API call: %s", api_call)

    try:
        async with aiohttp.ClientSession() as session:
            proxy_resp = await fetch_proxy(api_call, session)
    except Exception as e:
        logger.exception("Proxy error")
        await msg.edit_text("Failed to reach the proxy API.")
        return

    download_url, filename, filesize = extract_download_link(proxy_resp)
    if not download_url:
        await msg.edit_text("Couldn't extract a direct download link from the proxy response. Here's the raw response for debugging:")
        # provide readable excerpt (avoid huge outputs)
        import json
        try:
            snippet = json.dumps(proxy_resp, indent=2)[:3000]
        except Exception:
            snippet = str(proxy_resp)[:3000]
        await update.message.reply_text(f"```\n{snippet}\n```", parse_mode="Markdown")
        return

    await msg.edit_text("Got a download link. Deciding best way to deliver it to you...")
    # try to send file or link
    await send_download_link_or_file(update, context, download_url, filename, filesize)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi — send me a Terabox share URL (or use /download <url>) and I'll resolve it into a direct download link. "
        "If the file is small I may upload it directly; otherwise I'll return the link so you can download it yourself."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Please set TELEGRAM_BOT_TOKEN environment variable.")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("download", handle_download_cmd))
    # handle plain messages that look like a URL
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download_cmd))

    logger.info("Starting bot (polling)...")
    application.run_polling()


if __name__ == "__main__":
    main()
