from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

async def start(update, context):
    # Fetch user's first name for personalization
    user = update.message.chat.first_name or "User"  # Fallback to "User" if first name is missing

    # Create an inline keyboard layout
    keyboard = [
        [InlineKeyboardButton("📹 Download Video", callback_data="download_video")],
        [InlineKeyboardButton("🎵 Download Audio", callback_data="download_audio")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Reply with the welcome message and keyboard
    if update.message:
        await update.message.reply_text(
            f"Hi {user}! 🎉 Welcome to the YouTube Downloader Bot.\n\n"
            f"Please choose an option below:",
            reply_markup=reply_markup
        )


async def help_command(update: Update, context):
    commands = """
    Here are the available commands:
    /start - Start the bot
    /help - Show this help message
    /new_task - Start a new task
    """
    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(commands, reply_markup=reply_markup)


async def new_task(update: Update, context):
    # Reuse the start function to avoid duplication
    await start(update, context)
