FROM python:3.10-slim

# Устанавливаем Node.js (это исправит ошибку "No supported JavaScript runtime")
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Команда для запуска (порт 8080 как в логах)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main.py:app"]
