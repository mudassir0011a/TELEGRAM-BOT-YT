import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters,
)
from utils.downloader import process_link  # Assuming process_link is implemented in `utils.downloader`

# Initialize logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    keyboard = [
        [
            InlineKeyboardButton("🎥 Download Video", callback_data="download_video"),
            InlineKeyboardButton("🎵 Download Audio", callback_data="convert_audio"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Use the buttons below to get started:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button presses."""
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = query.data  # Save the user action
    if query.data == "download_video":
        await query.edit_message_text("Send me the link of the video to download.")
    elif query.data == "convert_audio":
        await query.edit_message_text("Send me the link of the video to convert to audio.")
    else:
        await query.edit_message_text("Unknown action.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles plain text messages (YouTube links)."""
    if "action" in context.user_data:
        await process_link(update, context)  # Call your `process_link` function
    else:
        await update.message.reply_text("Use /start to select an option first.")

def main():
    app = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run bot
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
