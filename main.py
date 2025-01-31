import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import os
import nest_asyncio
from telegram import BotCommand

# Patch the event loop
nest_asyncio.apply()

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

    # Clear the "done" state
    if "done" in context.user_data:
        context.user_data.pop("done")

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
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    user_name = update.effective_user.first_name
    logger.info(f"INFO - User {user_name} invoked the /help command.")

    await update.message.reply_text(
        "Here are the available commands:\n"
        "/start - Start the bot and explore options.\n"
        "/help - Get help about the bot.\n"
        "/history - View your download history.\n"
        "/reset_history - Clear's your download history.\n"
        "/video_download - Start downloading videos.\n"
        "/audio_download - Start downloading audio.\n"
        "/new_task - Start a new task.\n"
        "/done - Finish using the bot.\n\n"
        "Click on the buttons to download video or audio. Enjoy!"
    )

# /history command
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

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

# /reset_history command
async def reset_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    user_id = update.effective_user.id  # Get the unique user ID
    if user_id in user_history:
        del user_history[user_id]  # Remove the user's history
        logger.info(f"INFO - User {user_id}'s history has been reset.")
        await update.message.reply_text("Your download history has been successfully reset. ✅")
    else:
        await update.message.reply_text("You don't have any download history to reset. 😅")

# /video_download command
async def video_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    context.user_data["action"] = "video_download"
    await update.message.reply_text("Kindly provide the YouTube link for the video you wish to download.")

# /audio_download command
async def audio_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    context.user_data["action"] = "audio_download"
    await update.message.reply_text("Please share the YouTube link for the audio file you'd like to download.")

# /done command
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Thank you for using the bot, {user_name}! 😊\n"
        "If you need anything else, feel free to start again with /start.\n"
        "Have a great day! 👋"
    )
    # Mark the bot as "done"
    context.user_data["done"] = True

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

    # Check file size
    file_size = os.path.getsize(video_path)
    if file_size > 50 * 1024 * 1024:  # 50 MB limit
        logger.info(f"File size: {file_size / (1024 * 1024):.2f} MB")
        os.remove(video_path)  # Delete the file to save space
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="We're unfortunately sorry 😔, but the video file size exceeds 50 MB, which cannot be sent on Telegram. "
                 "Please try a smaller video or use a different tool."
        )
        return

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

    # Check file size
    file_size = os.path.getsize(audio_path)
    if file_size > 50 * 1024 * 1024:  # 50 MB limit
        logger.info(f"File size: {file_size / (1024 * 1024):.2f} MB")
        os.remove(audio_path)  # Delete the file to save space
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="We're unfortunately sorry 😔, but the audio file size exceeds 50 MB, which cannot be sent on Telegram. "
                 "Please try a smaller audio file or use a different tool."
        )
        return

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
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    url = update.message.text

    if not is_valid_youtube_url(url):
        await update.message.reply_text("The link you provided is invalid. Please send a valid YouTube URL.")
        return

    # Store the link in user_data
    context.user_data["url"] = url

    # If no action is selected, prompt the user to choose an option
    if "action" not in context.user_data:
        keyboard = [
            [InlineKeyboardButton("🎥 Video Download", callback_data="video_download")],
            [InlineKeyboardButton("🎵 Audio Download", callback_data="audio_download")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Please select an option to proceed:",
            reply_markup=reply_markup,
        )
        return

    # If action is already selected, process the link directly
    await handle_download(update, context)

# Handle download based on user action
async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_action = context.user_data.get("action")
    url = context.user_data.get("url")

    if not url:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please provide a valid YouTube link."
        )
        return

    if user_action == "video_download":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎥 Your video download is now in progress. Please hold on while we process your request."
        )
        await download_video(update, context, url)

    elif user_action == "audio_download":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎵 Your audio download is now in progress. Please hold on while we process your request."
        )
        await download_audio(update, context, url)

    # Clear the URL and action after processing
    context.user_data.pop("url", None)
    context.user_data.pop("action", None)

    # Show next steps
    keyboard = [
        [InlineKeyboardButton("🆕 New Task", callback_data="new_task")],
        [InlineKeyboardButton("✅ Done", callback_data="done")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="What would you like to do next?",
        reply_markup=reply_markup,
    )

# Callback for buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video_download":
        context.user_data["action"] = "video_download"
        await query.edit_message_text("🎥 Video Download selected. Processing your request...")
        if "url" in context.user_data:
            await handle_download(update, context)
        else:
            await query.edit_message_text("🎥 Video Download selected. Please share the YouTube link for the video you wish to download.")
    elif query.data == "audio_download":
        context.user_data["action"] = "audio_download"
        await query.edit_message_text("🎵 Audio Download selected. Processing your request...")
        if "url" in context.user_data:
            await handle_download(update, context)
        else:
            await query.edit_message_text("🎵 Audio Download selected. Please share the YouTube link for the audio file you'd like to download.")
    elif query.data == "new_task":
        keyboard = [
            [InlineKeyboardButton("🎥 Video Download", callback_data="video_download")],
            [InlineKeyboardButton("🎵 Audio Download", callback_data="audio_download")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Starting a new task! Choose an option below.", reply_markup=reply_markup)
    elif query.data == "done":
        await query.edit_message_text("Thank you for using the bot! 😉\nSee you next time! 👋")
        # Mark the bot as "done"
        context.user_data["done"] = True

# /new_task command
async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    keyboard = [
        [InlineKeyboardButton("🎥 Video Download", callback_data="video_download")],
        [InlineKeyboardButton("🎵 Audio Download", callback_data="audio_download")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Starting a new task! Choose an option below:", reply_markup=reply_markup)

# Unknown command
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the bot is in "done" state
    if "done" in context.user_data:
        await update.message.reply_text(
            "Please /start the bot to continue with your task."
        )
        return

    await update.message.reply_text(
        "Command not recognized. Please use /help to see the list of available commands."
    )

# Set up bot commands for the menu
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help about the bot"),
        BotCommand("history", "View your download history"),
        BotCommand("reset_history", "Clear's your download history"),
        BotCommand("video_download", "Download a video"),
        BotCommand("audio_download", "Download an audio file"),
        BotCommand("new_task", "Start a new task"),
        BotCommand("done", "Finish using the bot"),
    ]
    await application.bot.set_my_commands(commands)

# Main function
async def main():
    logger.info("\nSTARTING THE BOT\n")
    app = Application.builder().token(BOT_TOKEN).read_timeout(90).build()

    # Set commands in the menu
    await set_bot_commands(app)

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("reset_history", reset_history))
    app.add_handler(CommandHandler("video_download", video_download_command))
    app.add_handler(CommandHandler("audio_download", audio_download_command))
    app.add_handler(CommandHandler("new_task", new_task))
    app.add_handler(CommandHandler("done", done_command))
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
        logger.info("Bot stopped...")