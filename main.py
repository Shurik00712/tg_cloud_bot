import logging
import os
from dotenv import load_dotenv
from UploadFileManager import UploadFileManager
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
UPLOAD_FILE, DECISION, CONFIRM = range(3)
async def start(update, context):
    user = update.effective_user
    context.user_data["can_upload"] = False
    text = f"""Привет, {user.first_name}!
    Я бот CLOUDATA!
    создатель SANYOK
    Мои команды:
    /start - начать
    /help - помощь
    /about - о боте
    /menu - показать меню"""
    await update.message.reply_text(text)
async def help_command(update, context):
    text = """
    /start - начать
    /help - помощь
    /about - о боте
    /menu - показать меню"""
    await update.message.reply_text(text)
async def about_command(update, context):
    text = """
    Этот бот может сохранить твои данные в облаке"""
    await update.message.reply_text(text)
async def menu_command(update, context):
    keyboard = [
        ['Загрузить данные']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите действие:',
        reply_markup=reply_markup
    )
def setup_bot(token):
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("menu", menu_command))
    conv_handler = UploadFileManager()
    application.add_handler(conv_handler.get_conversation_handler())
    application.add_handler(CommandHandler("cancel", conv_handler.cancel))
    # application.add_handler(MessageHandler(filters.TEXT, handle_message))
    # application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    # application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    # application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    return application 
def main():
    application = setup_bot(BOT_TOKEN)
    print("Бот стартует...")
    application.run_polling()
if __name__ == "__main__":
    main()