import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import yt_dlp

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Global dictionary to store user history
user_history = {}

# Start command
# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name  # User ka naam lene ke liye
    # Buttons create karna
    keyboard = [
        [InlineKeyboardButton("Video Download", callback_data="video_download")],
        [InlineKeyboardButton("Audio Download", callback_data="audio_download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Message bhejna
    await update.message.reply_text(
        f"Hi {user_name}! 👋\nWelcome to the YouTube Downloader Bot.\nPlease choose an option below:",
        reply_markup=reply_markup,
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "video_download":
        await query.edit_message_text("Please send the YouTube link to download the video using /video_download <link>.")
    elif query.data == "audio_download":
        await query.edit_message_text("Please send the YouTube link to download the audio using /audio_download <link>.")

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/video_download - Download a YouTube video\n"
        "/audio_download - Download YouTube audio\n"
        "/new_task - Create a new task\n"
        "/history - View your download history"
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
        await update.message.reply_text("Please provide a YouTube link like this: /video_download <link>")
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
                caption=f"Here is your video: {video_title}",
            )
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await update.message.reply_text("Failed to download the video. Please check the link and try again.")

# Audio download command
async def audio_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.split(" ", 1)
    if len(user_message) < 2:
        await update.message.reply_text("Please provide a YouTube link like this: /audio_download <link>")
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
                caption=f"Here is your audio: {audio_title}",
            )
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        await update.message.reply_text("Failed to download the audio. Please check the link and try again.")

# New task command
async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Feature coming soon: Task management system!")

# History command
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_history or not user_history[user_id]:
        await update.message.reply_text("No history found! Start downloading something.")
    else:
        history_text = "\n".join(user_history[user_id])
        await update.message.reply_text(f"Your download history:\n{history_text}")

# Main function to run the bot
def main():
    # Create application instance
    app = Application.builder().token("8077274379:AAFawJIixuMK47T9RpxiMv0TC_FnYLA6LWI").build()

    # Add bot commands
    app.bot.set_my_commands([
        ("start", "Start the bot"),
        ("help", "Get help"),
        ("video_download", "Download a YouTube video"),
        ("audio_download", "Download YouTube audio"),
        ("new_task", "Create a new task"),
        ("history", "View your download history"),
    ])

    # Add command handlers
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("video_download", video_download))
    app.add_handler(CommandHandler("audio_download", audio_download))
    app.add_handler(CommandHandler("new_task", new_task))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CallbackQueryHandler(button_click))  # Button click handler add kiya

    # Start the bot
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
