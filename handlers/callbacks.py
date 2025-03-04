from telegram import Update
from telegram.ext import ContextTypes
from handlers.history import show_history
from utils.downloader import estimate_file_size, download_video_async
from yt_dlp import YoutubeDL

import os

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback button press

    if query.data == "download_video":
        context.user_data["action"] = "download_video"
        await query.edit_message_text("Send me the YouTube link to download the video.")
    elif query.data == "download_audio":
        context.user_data["action"] = "convert_audio"
        await query.edit_message_text("Send me the YouTube link to convert to audio.")
    elif query.data == "view_history":
        await query.edit_message_text("Your download history will appear here (Feature under development).")
    elif query.data == "help":
        await query.edit_message_text("Here are the available commands:\n/video_download - Download a video\n/audio_download - Download audio")
    else:
        await query.edit_message_text("Unknown action. Please try again.")


async def start_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the download of a video or audio file.
    """
    video_url = update.message.text  # Fetch user-provided URL
    if not video_url:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a valid YouTube URL.")
        return

    # Set format based on user action
    if context.user_data.get("action") == "convert_audio":
        format_id = "bestaudio"  # For audio downloads
    else:
        format_id = "18"  # Default format for video downloads

    # Notify user of the process start
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your request...")

    # Estimate file size
    estimated_size = estimate_file_size(video_url, format_id)
    if estimated_size != -1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Estimated file size: ~{estimated_size:.2f} MB"
        )
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Unable to estimate file size, continuing...")

    # Ensure downloads directory exists
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        # Download the video or audio
        file_path = await download_video_async(video_url, format_id, update, context)

        # Send the file to the user
        if os.path.exists(file_path):
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))
            os.remove(file_path)  # Clean up after sending the file
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to retrieve the file.")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"An error occurred: {e}")


async def download_video_async(video_url: str, format_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Downloads a video or audio file asynchronously.
    Returns the file path of the downloaded content.
    """
    options = {
        'format': format_id,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            return file_path
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Download error: {e}")
        return ""
