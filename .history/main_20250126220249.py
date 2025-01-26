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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global dictionary to store user history
user_history = {}

# Bot token
BOT_TOKEN = "8077274379:AAFawJIixuMK47T9RpxiMv0TC_FnYLA6LWI"  # Replace with your actual BotFather token.

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

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
        "/history - View your download history.\n\n"
        "Click on the buttons to download video or audio.\nEnjoy!"
    )

# Validate YouTube URL
def is_valid_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

# Download YouTube video
def download_video(url: str):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get("title", "video")
        video_path = ydl.prepare_filename(info)
        return video_title, video_path

# Download YouTube audio
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
        audio_path = ydl.prepare_filename(info).replace(".webm", ".mp3")
        return audio_title, audio_path

# Process the YouTube link
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_action = context.user_data.get("action")
    url = update.message.text

    if not user_action:
        await update.message.reply_text("Please choose an option first: Video or Audio Download.")
        return

    if not is_valid_youtube_url(url):
        await update.message.reply_text("The link you provided is invalid. Please send a valid YouTube URL.")
        return

    user_id = update.effective_user.id
    await update.message.reply_text("Processing your download. Please wait...")

    try:
        if user_action == "video_download":
            video_title, video_path = download_video(url)
            user_history.setdefault(user_id, []).append(f"Video: {video_title}")

            # Send the video
            with open(video_path, "rb") as video_file:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video_file,
                    caption=f"Your video titled '{video_title}' has been downloaded successfully!\nEnjoy!"
                )
        elif user_action == "audio_download":
            audio_title, audio_path = download_audio(url)
            user_history.setdefault(user_id, []).append(f"Audio: {audio_title}")

            # Send the audio
            with open(audio_path, "rb") as audio_file:
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    caption=f"Your audio titled '{audio_title}' has been downloaded successfully!\nEnjoy!"
                )

        # After success, provide options for a new task
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data="new_task")],
            [InlineKeyboardButton("Done", callback_data="done")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error processing download: {e}")
        await update.message.reply_text("Sorry, an error occurred while downloading. Please try again.")

        # Provide options for retrying or ending
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data="new_task")],
            [InlineKeyboardButton("Done", callback_data="done")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

# View download history
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_history or not user_history[user_id]:
        await update.message.reply_text("No history found. Start downloading something to see it here!")
    else:
        history_text = "\n".join(user_history[user_id])
        await update.message.reply_text(f"Here is your download history:\n{history_text}")

# Handle button clicks
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video_download":
        await query.edit_message_text("Please send the YouTube link for the **video download**.")
        context.user_data["action"] = "video_download"
    elif query.data == "audio_download":
        await query.edit_message_text("Please send the YouTube link for the **audio download**.")
        context.user_data["action"] = "audio_download"
    elif query.data == "new_task":
        await query.edit_message_text("Starting a new task! Choose an option below.")
        await start(update, context)
    elif query.data == "done":
        await query.edit_message_text("Thank you for using the bot! See you next time!")

# Handle unknown commands
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Command not recognized. Please use /help to see the list of available commands."
    )

# Main function to run the bot
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Start the bot
    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
