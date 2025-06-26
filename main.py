import os
from dotenv import load_dotenv
from typing import Final
from telegram import Update
from telegram.ext import Application,CommandHandler,MessageHandler,filters,ContextTypes

load_dotenv()
Token: Final = os.getenv('TOKEN')
Bot_username: Final = os.getenv('BOT_USERNAME')

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт, Я поки не маю функціоналу і знаходжусь на стадії розробки, буду готовий за декілька днів :)')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Кастомна команда')

# Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'телеграм' in processed:
        return 'бот'

    return 'Я поки не розумію тебе'

#
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text : str = update.message.text

    print(f'User: ({update.message.chat.id}) in {message_type}: "{text}"')

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

# Log
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(Token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT,handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)