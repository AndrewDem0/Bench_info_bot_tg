import os
import config
from dotenv import load_dotenv
from typing import Final
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()
Token: Final = os.getenv('TOKEN')
Bot_username: Final = os.getenv('BOT_USERNAME')

# Commands
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("📄 PDF", callback_data="show_pdf"),
        InlineKeyboardButton("▶️ YouTube", callback_data="show_youtube")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Оберіть формат історії:',
        reply_markup = reply_markup
    )
#
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт, Я поки не маю функціоналу і знаходжусь на стадії розробки, буду готовий за декілька днів :)')
#
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Кастомна команда')

# Responses


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'телеграм' in processed:
        return 'бот'
    
    elif 'r2' in processed:
        return 'd2'

    return 'Я поки не розумію тебе'


#
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    message_type: str = update.message.chat.type
    text : str = update.message.text

    print(f'User: ({user.id}, @{user.username}) in {message_type}: "{text}"')

    if message_type == 'group':
        if Bot_username in text:
            new_text : str = text.replace(Bot_username, '').strip()
            response : str = handle_response(new_text)
        else:
            return
    else:
        response : str = handle_response(text)

    print('Bot: ', response)
    await update.message.reply_text(response)
#
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    await query.answer()
    
    if query.data == "show_pdf":
        with open(config.PDF_PATH, "rb") as f:
            await query.message.reply_document(document = f, caption = "Ось твоя історія у форматі PDF")

    elif query.data == "show_youtube":
        await query.message.reply_text(config.YOUTUBE_LINK)
    
    user = query.from_user
    chat = query.message.chat
    print(f'User: ({user.id}, @{user.username}) in chat {chat.id}: pressed "{query.data}"')
    
# Log
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    
    
if __name__ == '__main__':
    print('Starting bot...')
    
    
    app = Application.builder().token(Token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('history', history_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT,handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval = 0.5)