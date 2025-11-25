FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

ENV PORT=8000

CMD gunicorn main:app --workers 1 --bind 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker --timeout 200
