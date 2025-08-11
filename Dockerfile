FROM python:3.10-slim

# reduce image size and memory usage
ENV PYTHONUNBUFFERED=1 \
    LD_BIND_NOW=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py /app/
COPY .env.example /app/.env

CMD ["python", "bot.py"]
