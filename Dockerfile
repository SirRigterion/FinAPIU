FROM python:3.12-slim AS base
WORKDIR /app

# Устанавливаем netcat-openbsd и обновляем pip
RUN apt-get update && apt-get install -y netcat-openbsd && \
    pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
