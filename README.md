1) Fill environment variables in Koyeb dashboard (API_ID, API_HASH, BOT_TOKEN or SESSION).

2) Build & push image to a registry (or let Koyeb build from this repo):
   - If local: docker build -t mymusicbot:latest .
   - Push to Docker Hub or Git registry.

3) On Koyeb, create a new app using your image (or connect GitHub repo). Set the container to run `python bot.py`.

4) Resource tips for 512MB:
   - Use a single replica.
   - Keep logs minimal.
   - Set restart on failure only.

5) Permissions in group:
   - Add the bot/user to the group.
   - Promote it to admin with invite, manage voice chat permissions.

6) Test with `/play <youtube link or name>`.

Troubleshooting:
 - If you hit memory OOM, enable swap in Koyeb (if available) or lower yt-dlp format to smaller bitrate.
 - If ffmpeg errors occur, ensure ffmpeg present in image (see Dockerfile).
