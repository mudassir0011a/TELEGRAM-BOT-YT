import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import os
import nest_asyncio

nest_asyncio.apply()  # Patch the event loop

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("__main__")

# Bot token
BOT_TOKEN = "8077274379:AAFawJIixuMK47T9RpxiMv0TC_FnYLA6LWI"

# Ensure the downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Dictionary to store user-specific download history
user_history = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    logger.info(f"User {user_name} started the bot.")
    keyboard = [
        [InlineKeyboardButton("🎥 Video Download", callback_data="video_download")],
        [InlineKeyboardButton("🎵 Audio Download", callback_data="audio_download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Hi {user_name}! 😎,\n\n"
        "Welcome to the YouTube Downloader Bot!\n\n"
        "Please choose an option below: ⬇️",
        reply_markup=reply_markup,
    )

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Help command invoked.")
    await update.message.reply_text(
        "Here are the available commands:\n"
        "/start - Start the bot and explore options.\n"
        "/help - Get help about the bot.\n"
        "/history - View your download history.\n"
        "/video_download - Start downloading videos.\n"
        "/audio_download - Start downloading audio.\n"
        "/new_task - Start a new task.\n\n"
        "Click on the buttons to download video or audio. Enjoy!"
    )

# /history command
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history_list = user_history.get(user_id, [])
    logger.info(f"User {update.effective_user.first_name} checked their download history.")

    if not history_list:
        await update.message.reply_text("You don't have any download history yet.")
    else:
        history_text = "Here is your 📜 download history:\n\n"
        for i, entry in enumerate(history_list, start=1):
            history_text += f"{i}. {entry}\n"
        await update.message.reply_text(history_text)

# Validate YouTube URL
def is_valid_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

# Download video
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        logger.info(f"Starting video download for URL: {url}")
        ydl_opts = {
            "format": "best",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get("title", "video")
            video_path = ydl.prepare_filename(info)

        user_id = update.effective_user.id
        user_history.setdefault(user_id, []).append(f"Video: {video_title}")

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(video_path, "rb"),
            caption=f"Your video titled '{video_title}' has been downloaded successfully!",
        )
        logger.info(f"Video '{video_title}' downloaded successfully for user {update.effective_user.first_name}.")
    except Exception as e:
        logger.error(f"Error downloading video: {e}")

# Download audio
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        logger.info(f"Starting audio download for URL: {url}")
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

        user_id = update.effective_user.id
        user_history.setdefault(user_id, []).append(f"Audio: {audio_title}")

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(audio_path, "rb"),
            caption=f"Your audio titled '{audio_title}' has been downloaded successfully!",
        )
        logger.info(f"Audio '{audio_title}' downloaded successfully for user {update.effective_user.first_name}.")
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")

# Process YouTube link
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_action = context.user_data.get("action")
    url = update.message.text

    if not user_action:
        await update.message.reply_text("Please choose an option first: Video or Audio Download.")
        return

    if not is_valid_youtube_url(url):
        await update.message.reply_text("The link you provided is invalid. Please send a valid YouTube URL.")
        return

    if user_action == "video_download":
        await update.message.reply_text("🎥 Your video download is now in progress. Please hold on while we process your request.")
        try:
            await download_video(update, context, url)
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            await update.message.reply_text("Sorry, an error occurred while downloading the video.")
    elif user_action == "audio_download":
        await update.message.reply_text("🎵 Your audio download is now in progress. Please hold on while we process your request.")
        try:
            await download_audio(update, context, url)
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            await update.message.reply_text("Sorry, an error occurred while downloading the audio.")

# Main function
async def main():
    logger.info("Starting the bot...")
    app = Application.builder().token(BOT_TOKEN).read_timeout(30).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))

    logger.info("Bot is running. Waiting for user interactions...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
