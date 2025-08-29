import os
import config
import hashlib
import json
from dotenv import load_dotenv
from typing import Final
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

admin_waiting_users : set = set()

load_dotenv()
Token: Final = os.getenv('TOKEN')
Bot_username: Final = os.getenv('BOT_USERNAME')

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print(f'New chat started by user: ({user.id}, @{user.username})')
    
    keyboard = [
        [KeyboardButton("📖 Історія створення лавки")],
        [KeyboardButton("💬 Зв'язатися з розробником")],
        [KeyboardButton("🌐 Громадська активність")]
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True)

    await update.message.reply_text(
        "Привіт! 👋 Натисни кнопку нижче, щоб почати:",
        reply_markup = reply_markup
    )
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
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id =update.message.from_user.id
    admin_waiting_users.add(user_id)
    
    print(f'User: ({user.id}, @{user.username}) tries to access admin panel')
    
    await update.message.reply_text('Введіть пароль для доступу до адмін-панелі:')
#
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Кастомна команда')
#

# Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()
    
    if "💬 зв'язатися з розробником" in processed:
        return "Шукайте за тегом👇\n" + "@F4076 "
    elif '🌐 громадська активність' in processed:
        return "Переходьте за посиланням👇\n"+"https://t.me/teremkyppua"
    
    return 'Оберіть опцію з меню'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id: int = update.message.from_user.id
    message_type: str = update.message.chat.type
    text: str = update.message.text
    
    if user_id in admin_waiting_users:
        return
    
    print(f'User: ({user.id}, @{user.username}) in {message_type}: "{text}"')

    response = None  # <-- важливо!

    if message_type == 'group':
        if Bot_username in text:
            new_text: str = text.replace(Bot_username, '').strip()
            response = handle_response(new_text)
        else:
            return
    elif text == "📖 Історія створення лавки":
        await history_command(update, context)
    else:
        response = handle_response(text)

    if response:
        print('Bot: ', response)
        await update.message.reply_text(response)
#
async def handle_admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text : str = update.message.text.strip()
    
    if user_id not in admin_waiting_users:
        return
    
    hashed_input = hashlib.sha256(text.encode()).hexdigest()
    if hashed_input == config.ADMIN_PASSWORD_HASH:
        await update.message.reply_text("Пароль вірний ✅ Ви увійшли в адмін-панель")
    else:
        await update.message.reply_text("Невірний пароль ❌")
    
    admin_waiting_users.remove(user_id)
    
#
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    await query.answer()
    
    if query.data == "show_pdf":
        await query.message.delete()
        with open(config.PDF_PATH, "rb") as f:
            await query.message.reply_document(document = f, caption = "Ось історія у форматі PDF👆\n")

    elif query.data == "show_youtube":
        await query.message.delete()
        await query.message.reply_text("Ось історія у форматі YouTube👇\n\n" + config.YOUTUBE_LINK)
    
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
    app.add_handler(CommandHandler('admin', admin_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_password))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval = 0.5)