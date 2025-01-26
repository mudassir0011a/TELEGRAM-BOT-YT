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
        with open(video_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"Your video titled '{video_title}' has been downloaded successfully!\nThank you for using the bot."
            )
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
        with open(audio_path, "rb") as audio_file:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=audio_file,
                caption=f"Your audio titled '{audio_title}' has been processed and downloaded!\nEnjoy your music."
            )
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
    application = Application.builder().token("YOUR_BOT_TOKEN_HERE").build()
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help information"),
        BotCommand("about", "Learn about this bot"),
        BotCommand("support", "Contact support"),
    ])
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("support", support_command))

    print("Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())