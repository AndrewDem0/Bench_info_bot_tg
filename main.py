import os
import config
import hashlib
import json
from dotenv import load_dotenv
from typing import Final
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

admin_waiting_users : set = set()
authorized_admins : set = set()

load_dotenv()
Token: Final = os.getenv('TOKEN')
Bot_username: Final = os.getenv('BOT_USERNAME')

#Json
class StatsManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self) -> dict:
        if not os.path.exists(self.file_path):
            return {"users":{}}
        with open(self.file_path, "r", encoding = "utf-8") as f:
            return json.load(f)
    
    def save_data(self):
        with open(self.file_path, "w", encoding = "utf-8") as f:
            json.dump(self.data, f, indent = 4, ensure_ascii = False)

    def update_user(self, username : str):
        if username not in self.data["users"]:
            self.data["users"][username] = {"total": 0, "weekly": 0}
        self.data["users"][username]["total"] += 1
        self.data["users"][username]["weekly"] += 1
        self.save_data()
        
    def get_user_stats(self, username : str) -> dict:
        return self.data["users"].get(username, {"total": 0, "weekly": 0})
    
    def get_all_stats_text(self) -> str:

        if not self.data["users"]:
            return "Поки що немає жодного користувача."
    
        lines = ["📊 Статистика використання боту:\n"]
    
        for username, stats in self.data["users"].items():
            lines.append(f"👤 {username} | all: {stats['total']} | This week: {stats['weekly']}")
    
        return "\n".join(lines)
    
    def reset_weekly(self):
        for user in self.data["users"].values():
            user["weekly"] = 0
        self.save_data()

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
    admin_waiting_users.add(user.id)
    
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
    username = user.username or str(user.id)
    message_type: str = update.message.chat.type
    text: str = update.message.text
    
    if user.id not in authorized_admins:
        print(f'User: ({user.id}, @{user.username}) in {message_type}: "{text}"')
    
    stats_manager.update_user(username)

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
    user = update.message.from_user
    text : str = update.message.text.strip()
    
    if user.id not in admin_waiting_users:
        return await handle_message(update, context)
    
    hashed_input = hashlib.sha256(text.encode()).hexdigest()
    
    if hashed_input == config.ADMIN_PASSWORD_HASH:
        authorized_admins.add(user.id)
        await show_admin_menu(update)
    else:
        await update.message.reply_text("Невірний пароль ❌")
    
    admin_waiting_users.remove(user.id)
#
async def show_admin_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("📊 Відвідуваність", callback_data="admin_stats")],
        [InlineKeyboardButton("🗑 Очистити тиждень", callback_data="admin_reset_weekly")],
        [InlineKeyboardButton("❌ Вийти", callback_data="admin_logout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Адмін-панель:", reply_markup = reply_markup)
#
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    await query.answer()
    
    if user.id in authorized_admins:
        if query.data == "admin_stats":
            stats_text = stats_manager.get_all_stats_text()
            await query.message.reply_text(stats_text)
            await show_admin_menu(query.message)
            return
        
        elif query.data == "admin_reset_weekly":
            stats_manager.reset_weekly()
            await query.message.reply_text("Тижневі дані очищено ✅")
            await show_admin_menu(query.message)
            return
        
        elif query.data == "admin_logout":
            authorized_admins.remove(user.id)
            await query.message.reply_text("Ви вийшли з адмін-панелі ❌")
            return await history_command(update, context)

    
    if query.data == "show_pdf":
        await query.message.delete()
        with open(config.PDF_PATH, "rb") as f:
            await query.message.reply_document(document = f, caption = "Ось історія у форматі PDF👆\n")

    elif query.data == "show_youtube":
        await query.message.delete()
        await query.message.reply_text("Ось історія у форматі YouTube👇\n\n" + config.YOUTUBE_LINK)
    
    if user.id not in authorized_admins:
        chat = query.message.chat
        print(f'User: ({user.id}, @{user.username}) in chat {chat.id}: pressed "{query.data}"')
    
# Log
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    
    
if __name__ == '__main__':
    print('Starting bot...')
    
    # JSON stats manager
    stats_manager = StatsManager(config.JSON_DB_PATH)
    
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