import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os
import yt_dlp
import nest_asyncio

nest_asyncio.apply()  # To avoid asyncio event loop issues

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8077274379:AAFawJIixuMK47T9RpxiMv0TC_FnYLA6LWI"  # Replace with your actual token

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Video Download", callback_data="video_download")],
        [InlineKeyboardButton("Audio Download", callback_data="audio_download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the YouTube Downloader Bot!\nPlease choose an option below:",
        reply_markup=reply_markup,
    )


# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/history - Show your download history\n"
        "/video_download - Download a video\n"
        "/audio_download - Download audio\n"
        "/new_task - Start a new task"
    )


# Validate YouTube URL
def is_valid_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


# Process link
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_action = context.user_data.get("action")
    url = update.message.text

    if not user_action:
        await update.message.reply_text("Please select Video or Audio Download first.")
        return

    if not is_valid_youtube_url(url):
        await update.message.reply_text("Invalid YouTube URL. Please try again.")
        return

    await update.message.reply_text("Processing your download. Please wait...")

    try:
        if user_action == "video_download":
            await download_video(update, context, url)
        elif user_action == "audio_download":
            await download_audio(update, context, url)

        # After successful download, show New Task/Done buttons
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data="new_task")],
            [InlineKeyboardButton("Done", callback_data="done")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error processing download: {e}")
        await update.message.reply_text("An error occurred while processing your request.")


# Download video
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    ydl_opts = {
        "format": "best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get("title", "video")
        video_path = ydl.prepare_filename(info)

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(video_path, "rb"),
        caption=f"Your video titled '{video_title}' has been downloaded successfully!",
    )


# Download audio
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_title = info.get("title", "audio")
        audio_path = ydl.prepare_filename(info).replace(".webm", ".mp3")

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(audio_path, "rb"),
        caption=f"Your audio titled '{audio_title}' has been downloaded successfully!",
    )


# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video_download":
        await query.edit_message_text("Please send the YouTube link for the video download.")
        context.user_data["action"] = "video_download"

    elif query.data == "audio_download":
        await query.edit_message_text("Please send the YouTube link for the audio download.")
        context.user_data["action"] = "audio_download"

    elif query.data == "new_task":
        keyboard = [
            [InlineKeyboardButton("Video Download", callback_data="video_download")],
            [InlineKeyboardButton("Audio Download", callback_data="audio_download")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose an option below:", reply_markup=reply_markup)

    elif query.data == "done":
        await query.edit_message_text("Thank you for using the bot! Have a great day!")


# /history command
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("History feature is not yet implemented.")


# Unknown command handler
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Use /help to see available commands.")


# Main function to run the bot
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(CommandHandler("video_download", start))
    application.add_handler(CommandHandler("audio_download", start))
    application.add_handler(CommandHandler("new_task", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot started...")
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
