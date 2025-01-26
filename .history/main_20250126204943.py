import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Global dictionary to store user history
user_history = {}

# Bot token (Replace 'YOUR_BOT_TOKEN' with your actual token from BotFather)
BOT_TOKEN = "8077274379:AAFawJIixuMK47T9RpxiMv0TC_FnYLA6LWI"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    keyboard = [
        [InlineKeyboardButton("Video Download", callback_data="video_download")],
        [InlineKeyboardButton("Audio Download", callback_data="audio_download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Hi {user_name},\n\n"
        "Welcome to the YouTube Downloader Bot!\n\n"
        "Please choose an option below:",
        reply_markup=reply_markup,
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Here are the available commands:\n"
        "/start - Start the bot and explore options.\n"
        "/video_download <YouTube URL> - Download a video from YouTube.\n"
        "/audio_download <YouTube URL> - Download audio from YouTube.\n"
        "/history - View your download history.\n\n"
        "Feel free to explore and enjoy!"
    )

# Function to download YouTube video
def download_video(url: str):
    ydl_opts = {
        "format": "mp4",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get("title", "video")
        video_path = ydl.prepare_filename(info)
        return video_title, video_path

# Function to download YouTube audio
def download_audio(url: str):
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
        audio_path = ydl.prepare_filename(info)
        return audio_title, audio_path.replace(".webm", ".mp3")

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video_download":
        await query.edit_message_text("Please send a YouTube link to proceed 🫣")
    elif query.data == "audio_download":
        await query.edit_message_text("Please send a YouTube link to proceed 🫣")

# Video download command
async def video_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.split(" ", 1)
    if len(user_message) < 2:
        await update.message.reply_text(
            "The link you provided is invalid. \n"
            "Please ensure you’ve entered a valid YouTube URL and try again."
        )
        return

    url = user_message[1]
    user_id = update.effective_user.id

    await update.message.reply_text("Processing your video download. Please wait...")
    try:
        video_title, video_path = download_video(url)
        user_history.setdefault(user_id, []).append(f"Video: {video_title}")

        await update.message.reply_text(
            f"Your video '{video_title}' is ready! Sending it now..."
        )

        with open(video_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"Your video titled '{video_title}' has been downloaded successfully!\nThank you for using the bot."
            )

        # Send new buttons
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data="new_task")],
            [InlineKeyboardButton("History", callback_data="history")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await update.message.reply_text(
            "Sorry, we encountered an error while processing your request. \n"
            "Please check your link and try again."
        )

# Audio download command
async def audio_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.split(" ", 1)
    if len(user_message) < 2:
        await update.message.reply_text(
            "The link you provided is invalid. \n"
            "Please ensure you’ve entered a valid YouTube URL and try again."
        )
        return

    url = user_message[1]
    user_id = update.effective_user.id

    await update.message.reply_text("Processing your audio download. Please wait...")
    try:
        audio_title, audio_path = download_audio(url)
        user_history.setdefault(user_id, []).append(f"Audio: {audio_title}")

        await update.message.reply_text(
            f"Your audio '{audio_title}' is ready! Sending it now..."
        )

        with open(audio_path, "rb") as audio_file:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=audio_file,
                caption=f"Your audio titled '{audio_title}' has been processed and downloaded!\nEnjoy your music."
            )

        # Send new buttons
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data="new_task")],
            [InlineKeyboardButton("History", callback_data="history")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        await update.message.reply_text(
            "Sorry, we encountered an error while processing your request. \n"
            "Please check your link and try again."
        )

# History command
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_history or not user_history[user_id]:
        await update.message.reply_text(
            "No history found. Start downloading something to see it here!"
        )
    else:
        history_text = "\n".join(user_history[user_id])
        await update.message.reply_text(
            f"Here is your download history:\n{history_text}"
        )

# Unknown command handler
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Command not recognized. \n"
        "Please use /help to see the list of available commands."
    )

# Main function to run the bot
async def main():
    try:
        # Create application instance
        app = Application.builder().token(BOT_TOKEN).build()

        # Add bot commands
        await app.bot.set_my_commands([
            ("start", "Start the bot"),
            ("help", "Get help"),
            ("video_download", "Download a YouTube video"),
            ("audio_download", "Download YouTube audio"),
            ("history", "View your download history"),
        ])

        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("video_download", video_download))
        app.add_handler(CommandHandler("audio_download", audio_download))
        app.add_handler(CommandHandler("history", history))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

        # Start the bot
        print("Bot is running...")
        await app.run_polling()

    except Exception as e:
        logger.error(f"Failed to start the bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
