from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Display Download History
async def show_history(update, context):
    chat_id = update.callback_query.message.chat_id if update.callback_query else None
    if not chat_id:
        await update.message.reply_text("Error: Unable to fetch callback query.")
        return

    download_history = context.bot_data.get("download_history", {})
    if not isinstance(download_history, dict):
        download_history = {}

    history = download_history.get(chat_id, [])

    if not history:
        text = "You have no download history."
    else:
        MAX_HISTORY_ITEMS = 10
        text = "Your download history:\n\n"
        for i, record in enumerate(history[:MAX_HISTORY_ITEMS], 1):
            text += f"{i}. {record}\n"

        if len(history) > MAX_HISTORY_ITEMS:
            text += f"\n...and {len(history) - MAX_HISTORY_ITEMS} more entries."

    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
