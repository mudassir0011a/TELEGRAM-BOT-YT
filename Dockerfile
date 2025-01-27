FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

CMD ["python", "main.py"]

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg
