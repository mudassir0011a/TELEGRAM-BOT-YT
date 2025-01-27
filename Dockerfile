# Base Image
FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy project files
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install -r /app/requirements.txt

# Set working directory
COPY . /app
WORKDIR /app

# Start the bot
CMD ["python", "bot.py"]
