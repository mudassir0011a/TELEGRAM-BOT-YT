FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/
COPY cookies.txt /app/cookies.txt  

# Install ffmpeg and cleanup
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

CMD ["python", "main.py"]