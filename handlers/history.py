from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Display Download History
async def show_history(update, context):
    chat_id = update.callback_query.message.chat_id
    download_history = context.bot_data.get("download_history", {})
    history = download_history.get(chat_id, [])

    if not history:
        text = "You have no download history."
    else:
        text = "Your download history:\n\n"
        for i, record in enumerate(history, 1):
            text += f"{i}. {record}\n"

    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
