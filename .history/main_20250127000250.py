import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import os
import nest_asyncio

nest_asyncio.apply()  # Patch the event loop

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),  # Logs to a file
        logging.StreamHandler(),        # Logs to the terminal
    ],
)

logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "8077274379:AAFawJIixuMK47T9RpxiMv0TC_FnYLA6LWI"  # Replace with your BotFather token

# Ensure the downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Dictionary to store user-specific download history
user_history = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    logger.info(f"INFO - User {user_name} (ID: {user_id}) started the bot.")

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
    user_name = update.effective_user.first_name
    logger.info(f"INFO - User {user_name} invoked the /help command.")

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
    user_id = update.effective_user.id  # Get the unique user ID
    history_list = user_history.get(user_id, [])  # Fetch the user's history or an empty list

    if not history_list:
        await update.message.reply_text("You don't have any download history yet.")
    else:
        # Format the history into a readable format
        history_text = "Here is your 📜 download history:\n\n"
        for i, entry in enumerate(history_list, start=1):
            history_text += f"{i}. {entry}\n"
        await update.message.reply_text(history_text)

# /video_download command
async def video_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = "video_download"
    await update.message.reply_text("Kindly provide the YouTube link for the video you wish to download.")

# /audio_download command
async def audio_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = "audio_download"
    await update.message.reply_text("Please share the YouTube link for the audio file you'd like to download.")

# Validate YouTube URL
def is_valid_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

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

    # Save to history
    user_id = update.effective_user.id
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(f"Video: {video_title}")

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

    # Save to history
    user_id = update.effective_user.id
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(f"Audio: {audio_title}")

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(audio_path, "rb"),
        caption=f"Your audio titled '{audio_title}' has been downloaded successfully!",
    )

# Process YouTube link
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_action = context.user_data.get("action")  # Retrieve user action
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

    # Show next steps
    keyboard = [
        [InlineKeyboardButton("🆕 New Task", callback_data="new_task")],
        [InlineKeyboardButton("✅ Done", callback_data="done")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

# Callback for buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video_download":
        await query.edit_message_text("Kindly provide the YouTube link to initiate the video download process")
        context.user_data["action"] = "video_download"
    elif query.data == "audio_download":
        await query.edit_message_text("Kindly provide the YouTube link to initiate the audio download process..")
        context.user_data["action"] = "audio_download"
    elif query.data == "new_task":
        keyboard = [
            [InlineKeyboardButton("🎥 Video Download", callback_data="video_download")],
            [InlineKeyboardButton("🎵 Audio Download", callback_data="audio_download")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Starting a new task! Choose an option below.", reply_markup=reply_markup)
    elif query.data == "done":
        await query.edit_message_text("Thank you for using the bot! 😉\nSee you next time! 👋")

# /new_task command
async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎥 Video Download", callback_data="video_download")],
        [InlineKeyboardButton("🎵 Audio Download", callback_data="audio_download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Starting a new task! Choose an option below:", reply_markup=reply_markup)

# Unknown command
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Command not recognized. Please use /help to see the list of available commands."
    )

# Main function
async def main():
    logger.info("\nSTARTING THE BOT\n")
    app = Application.builder().token(BOT_TOKEN).read_timeout(90).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("new_task", new_task))
    app.add_handler(CommandHandler("video_download", video_download_command))
    app.add_handler(CommandHandler("audio_download", audio_download_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("\nBOT HAS STARTED\n")
    logger.info("\nBOT IS RUNNING\n")
    logger.info("\nWAITING FOR USER INTERACTIONS...\n")

    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")