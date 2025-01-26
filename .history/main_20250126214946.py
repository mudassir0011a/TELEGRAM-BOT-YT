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

# Function to validate YouTube URL
def is_valid_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

# Function to download YouTube video
async def download_video(update, context):
    user_id = update.effective_chat.id
    message = await context.bot.send_message(chat_id=user_id, text="Processing your video download. Please wait...")

    try:
        # Simulate video download process
        await asyncio.sleep(5)  # Replace this with your actual video download logic

        # Simulate a successful video download
        video_file_path = "path/to/your/video.mp4"  # Replace with actual file path
        video_title = "Top 7 CRIME Suspense Thriller Movies in 2024"

        # Send the video to the user
        await context.bot.send_document(chat_id=user_id, document=open(video_file_path, 'rb'))
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Your video titled '{video_title}' has been downloaded successfully! Enjoy!"
        )

        # Add buttons for New Task and Done
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data='new_task')],
            [InlineKeyboardButton("Done", callback_data='done')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="What would you like to do next?", reply_markup=reply_markup)

    except Exception as e:
        # Delay before sending the error message
        await asyncio.sleep(3)  # Delay to ensure proper sequence
        await context.bot.send_message(
            chat_id=user_id,
            text="Sorry, an error occurred while downloading the video."
        )
        # Add buttons for New Task and Done
        keyboard = [
            [InlineKeyboardButton("New Task", callback_data='new_task')],
            [InlineKeyboardButton("Done", callback_data='done')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="What would you like to do next?", reply_markup=reply_markup)

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
        audio_path = ydl.prepare_filename(info).replace(".webm", ".mp3")
        return audio_title, audio_path

# Process video or audio download after the user sends the YouTube link
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_action = context.user_data.get("action")  # Retrieve user action
    url = update.message.text

    if not user_action:
        await update.message.reply_text("Please choose an option first: Video or Audio Download.")
        return

    if not is_valid_youtube_url(url):
        await update.message.reply_text("The link you provided is invalid. Please send a valid YouTube URL.")
        return

    user_id = update.effective_user.id
    if user_action == "video_download":
        await update.message.reply_text("Processing your video download. Please wait...")
        try:
            video_title, video_path = download_video(url)
            user_history.setdefault(user_id, []).append(f"Video: {video_title}")

            with open(video_path, "rb") as video_file:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video_file,
                    caption=f"Your video titled '{video_title}' has been downloaded successfully!\nEnjoy!"
                )
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            await update.message.reply_text("Sorry, an error occurred while downloading the video.")
    elif user_action == "audio_download":
        await update.message.reply_text("Processing your audio download. Please wait...")
        try:
            audio_title, audio_path = download_audio(url)
            user_history.setdefault(user_id, []).append(f"Audio: {audio_title}")

            with open(audio_path, "rb") as audio_file:
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    caption=f"Your audio titled '{audio_title}' has been downloaded successfully!\nEnjoy!"
                )
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            await update.message.reply_text("Sorry, an error occurred while downloading the audio.")

    # After task completion, show new buttons
    keyboard = [
        [InlineKeyboardButton("New Task", callback_data="new_task")],
        [InlineKeyboardButton("Done", callback_data="done")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

# History command
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_history or not user_history[user_id]:
        await update.message.reply_text("No history found. Start downloading something to see it here!")
    else:
        history_text = "\n".join(user_history[user_id])
        await update.message.reply_text(f"Here is your download history:\n{history_text}")

# Callback query handler for button clicks
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video_download":
        await query.edit_message_text("Please send the YouTube link for the **video download** 🫣")
        context.user_data["action"] = "video_download"  # Store action in user_data
    elif query.data == "audio_download":
        await query.edit_message_text("Please send the YouTube link for the **audio download** 🫣")
        context.user_data["action"] = "audio_download"  # Store action in user_data
    elif query.data == "new_task":
        await query.edit_message_text("Starting a new task! Choose an option below.")
        await start(update, context)  # Restart to show main buttons
    elif query.data == "done":
        await query.edit_message_text("Thank you for using the bot! See you next time!")

# Unknown command handler
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))  # Process YouTube links
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Start the bot
    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
