import logging
import os
from dotenv import load_dotenv
from UploadFileManager import UploadFileManager
from ShowFilemanager import ShowFileManager
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    user = update.effective_user
    context.user_data.clear()
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
    return ConversationHandler.END

async def help_command(update, context):
    text = """
/start - начать
/help - помощь
/about - о боте
/menu - показать меню"""
    await update.message.reply_text(text)
    return ConversationHandler.END

async def about_command(update, context):
    text = "Этот бот может сохранить твои данные в облаке"
    await update.message.reply_text(text)
    return ConversationHandler.END

async def menu_command(update, context):
    context.user_data.clear()
    
    keyboard = [
        ['Загрузить данные', 'Просмотреть файлы']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите действие:',
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel_command(update, context):
    if "curr" in context.user_data:
        if context.user_data["curr"] == "upload":
            if "file_file" not in context.user_data:
                text = "Вы ещё не начали загрузку файла"
                if "last_save" in context.user_data:
                    try:
                        os.remove(context.user_data["last_save"])
                        text = "Предыдущий файл удален"
                    except Exception as e:
                        logger.error(f"Ошибка при удалении файла: {e}")
                await update.message.reply_text(text)
            else:
                await update.message.reply_text("Загрузка файла отменена", reply_markup=ReplyKeyboardRemove())
            
            last_save = context.user_data.get("last_save")
            context.user_data.clear()
            if last_save is not None:
                context.user_data["last_save"] = last_save
                
        elif context.user_data["curr"] == "show":
            await update.message.reply_text("Просмотр файлов отменен", reply_markup=ReplyKeyboardRemove())
            context.user_data.clear()
    else:
        await update.message.reply_text("Нет активных операций для отмены")
    
    return ConversationHandler.END

async def handle_text_message(update, context):
    text = update.message.text
    if text == 'Загрузить данные':
        # Это будет перехвачено ConversationHandler UploadFileManager
        return
    elif text == 'Просмотреть файлы':
        # Это будет перехвачено ConversationHandler ShowFileManager
        return
    else:
        await update.message.reply_text("Используйте команды из меню или /menu")

def setup_bot(token):
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    
    upload_manager = UploadFileManager()
    show_manager = ShowFileManager()
    
    application.add_handler(upload_manager.get_conversation_handler(cancel_command, menu_command))
    application.add_handler(show_manager.get_conversation_handler(cancel_command))
    
    application.add_handler(CommandHandler("menu", menu_command))
    
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    return application

def main():
    application = setup_bot(BOT_TOKEN)
    print("Бот стартует...")
    application.run_polling()

if __name__ == "__main__":
    main()