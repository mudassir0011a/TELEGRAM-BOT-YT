from telegram import Update
from telegram.ext import ContextTypes
from handlers.history import show_history
from utils.downloader import estimate_file_size, download_video_async
from utils.downloader import estimate_file_size, download_video

import os

from telegram import Update
from telegram.ext import ContextTypes

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback button press

    if query.data == "download_video":
        # Set the action for downloading video
        context.user_data["action"] = "download_video"
        await query.edit_message_text("Send me the YouTube link to download the video.")
    elif query.data == "download_audio":
        # Set the action for downloading audio
        context.user_data["action"] = "convert_audio"
        await query.edit_message_text("Send me the YouTube link to convert to audio.")
    elif query.data == "view_history":
        # Mock response for history
        await query.edit_message_text("Your download history will appear here (Feature under development).")
    elif query.data == "help":
        await query.edit_message_text("Here are the available commands:\n/video_download - Download a video\n/audio_download - Download audio")
    else:
        await query.edit_message_text("Unknown action. Please try again.")

        await query.edit_message_text("Invalid action.")


async def start_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the download of a video file.
    """
    video_url = "USER_PROVIDED_URL"  # This will eventually come from user input
    format_id = "18"  # Default YouTube format ID, change based on user input if needed

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

    # Proceed with downloading the video asynchronously
    await download_video_async(video_url, format_id, update, context)


def get_actual_file_size(file_path: str) -> float:
    """
    Get the actual downloaded file size in MB.
    """
    try:
        size_in_bytes = os.path.getsize(file_path)
        return size_in_bytes / (1024 ** 2)  # Convert to MB
    except FileNotFoundError:
        return -1
