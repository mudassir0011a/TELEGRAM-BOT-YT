FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/
COPY cookies_netscape.txt /app/cookies.txt  

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

CMD ["python", "main.py"]