FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Koyeb любит порт 8080, поэтому ставим его
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]