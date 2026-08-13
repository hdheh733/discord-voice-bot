FROM python:3.10-slim

# تثبيت مكتبات الصوت و FFmpeg
RUN apt-get update && apt-get install -y ffmpeg git build-essential

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]