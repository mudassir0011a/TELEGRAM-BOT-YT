import os
import json
import logging
import asyncio
import subprocess
import yt_dlp as youtube_dl
from telegram import Update
from telegram.ext import ContextTypes

# Initialize logger
logger = logging.getLogger(__name__)


def estimate_file_size(video_url: str, format_id: str) -> float:
    """
    Estimate the file size of the video based on YT-DLP metadata.
    Returns the file size in MB, or -1 if not available.
    """
    try:
        command = ["yt-dlp", "--dump-json", "--format", format_id, video_url]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Error fetching metadata: {result.stderr}")
            return -1

        video_info = json.loads(result.stdout)

        # Get the requested format details
        format_info = next((f for f in video_info['formats'] if f['format_id'] == format_id), None)

        if 'filesize' in format_info:
            return format_info['filesize'] / (1024 ** 2)  # Convert bytes to MB
        elif 'tbr' in format_info and video_info.get('duration'):
            # Estimate size using tbr and duration
            tbr = format_info['tbr']  # Bitrate (kbps)
            duration = video_info['duration']  # Duration in seconds
            return (tbr * duration * 125) / (1024 ** 2)  # Size in MB
        else:
            return -1
    except Exception as e:
        logger.error(f"Error estimating file size: {e}")
        return -1


async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processes the user's URL and handles the requested action.
    """
    try:
        user_action = context.user_data.get("action")
        if not user_action:
            await update.message.reply_text("No action specified. Please choose 'Download Video' or 'Convert to Audio'.")
            return

        url = update.message.text.strip()
        if not url.startswith("http"):
            await update.message.reply_text("Please provide a valid YouTube URL.")
            return

        logger.info(f"Processing link: {url} for action: {user_action}")

        # Estimate file size using yt-dlp
        format_id = "18"  # Default video format
        estimated_size = estimate_file_size(url, format_id)

        if estimated_size != -1:
            await update.message.reply_text(f"Processing your request.\nEstimated file size: ~{estimated_size:.2f} MB")
        else:
            await update.message.reply_text("Unable to estimate file size. Proceeding with download...")

        # Execute user action
        if user_action == "download_video":
            await download_video_async(url, format_id, update, context)
        elif user_action == "convert_audio":
            await convert_to_audio(update, context, url)
        else:
            await update.message.reply_text("Invalid action.")
    except Exception as e:
        logger.error(f"Error in process_link: {e}")
        await update.message.reply_text(f"An error occurred: {e}")


async def download_video_async(video_url, format_id, update, context):
    """
    Asynchronous wrapper to download a video.
    """
    try:
        await download_video(update, context, video_url)
    except Exception as e:
        logger.error(f"Error in download_video_async: {e}")
        await update.message.reply_text(f"An error occurred during asynchronous video download: {e}")


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """
    Downloads the video using yt-dlp and sends it to the user.
    """
    try:
        await update.message.reply_text("Downloading video. Please wait...")

        output_template = "downloads/%(title)s.%(ext)s"
        options = {
            'format': 'best',
            'outtmpl': output_template,
            'quiet': True,
            'force_overwrites': True,
            'cookiefile': 'youtube_cookies.txt',  # Add cookies file for authentication
        }

        with youtube_dl.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # Get file size
        file_size = os.path.getsize(file_path) / (1024 ** 2)

        if file_size > 50:
            await update.message.reply_text(
                f"File downloaded successfully but exceeds Telegram's 50 MB limit.\nFile size: {file_size:.2f} MB."
            )
        else:
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(video_file)
            await update.message.reply_text(f"Video sent successfully! File size: {file_size:.2f} MB.")
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await update.message.reply_text(f"An error occurred while downloading video: {e}")


async def convert_to_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """
    Converts a YouTube video to audio and sends it to the user.
    """
    try:
        await update.message.reply_text("Converting video to audio. Please wait...")

        output_template = "downloads/%(title)s.%(ext)s"
        options = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
            ],
            'ffmpeg_location': 'C:\Users\atikm\Downloads\APPLICATIONS\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe',
            'cookiefile': 'youtube_cookies.txt',  # Add cookies file for authentication
        }

        with youtube_dl.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace(".webm", ".mp3")

        # Get file size
        file_size = os.path.getsize(file_path) / (1024 ** 2)

        if file_size > 50:
            await update.message.reply_text(
                f"Audio converted successfully but exceeds Telegram's 50 MB limit.\nFile size: {file_size:.2f} MB."
            )
        else:
            with open(file_path, "rb") as audio_file:
                await update.message.reply_audio(audio_file)
            await update.message.reply_text(f"Audio sent successfully! File size: {file_size:.2f} MB.")
    except Exception as e:
        logger.error(f"Error converting to audio: {e}")
        await update.message.reply_text(f"An error occurred while converting audio: {e}")
