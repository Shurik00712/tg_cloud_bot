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

WAITING_FOR_CODE = 1

async def start(update, context):
    user = update.effective_user
    
    if context.user_data.get("access_code"):
        access_code = context.user_data.get("access_code")
        context.user_data.clear()
        context.user_data["access_code"] = access_code
        
        text = f"""Привет, {user.first_name}!
Я бот CLOUDATA!
Мои команды:
/start - начать
/help - помощь
/about - о боте
/menu - показать меню"""
        await update.message.reply_text(text)
        return ConversationHandler.END
    else:
        context.user_data.clear()
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n"
            f"Я бот CLOUDATA!\n\n"
            f"🔐 **Для начала работы необходимо придумать код длиной не менее 20 знаков для шифровки файлов**\n\n"
            f"Пожалуйста, введите ваш код:",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_FOR_CODE

async def process_code_input(update, context):
    user_input = update.message.text.strip()
    if len(user_input)>=20:
        context.user_data["access_code"] = user_input
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение с кодом: {e}")
        
        await update.message.reply_text(
            f"**Код успешно принят!**\n\n"
            f"Теперь вы можете использовать все функции бота.\n\n"
            f"Мои команды:\n"
            f"/start - начать\n"
            f"/help - помощь\n"
            f"/about - о боте\n"
            f"/menu - показать меню",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "**Неверный формат кода!**\n\n"
            "Код должен содержать **не менее 20 символов**\n"
            "Пожалуйста, введите код еще раз:",
            parse_mode='Markdown'
        )
        return WAITING_FOR_CODE

async def help_command(update, context):
    """Показывает помощь"""
    if not context.user_data.get("access_code"):
        await update.message.reply_text(
            "**Сначала необходимо придумать код**\n\n"
            "Используйте /start для ввода кода.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    text = """
/start - начать
/help - помощь
/about - о боте
/menu - показать меню"""
    await update.message.reply_text(text)
    return ConversationHandler.END

async def about_command(update, context):
    """Показывает информацию о боте"""
    if not context.user_data.get("access_code"):
        await update.message.reply_text(
            "**Сначала необходимо придумать код**\n\n"
            "Используйте /start для ввода кода.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    text = "Этот бот может сохранить твои данные в облаке. Максимальный размер файла: 50 МБ"
    await update.message.reply_text(text)
    return ConversationHandler.END

async def menu_command(update, context):
    """Показывает меню"""
    if not context.user_data.get("access_code"):
        await update.message.reply_text(
            "**Сначала необходимо придумать код**\n\n"
            "Используйте /start для ввода кода.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    access_code = context.user_data["access_code"]
    context.user_data.clear()
    context.user_data["access_code"] = access_code
    
    keyboard = [
        ['📤 Загрузить',
        '📂 Просмотреть', 
        '🚪 Выйти из режима']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите действие:',
        reply_markup=reply_markup,
    )
    return ConversationHandler.END

async def cancel_command(update, context):
    """Отмена операций"""
    if not context.user_data.get("access_code"):
        await update.message.reply_text(
            "**Сначала необходимо придумать код**\n\n"
            "Используйте /start для ввода кода.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    current_mode = context.user_data.get("curr")
    
    mode_messages = {
        "upload": "загрузки файла",
        "show": "просмотра файлов",
    }
    
    if current_mode in mode_messages:
        message = f"Вы вышли из режима {mode_messages[current_mode]}"
        saved_code = context.user_data.get("access_code")
        context.user_data.clear()
        if saved_code:
            context.user_data["access_code"] = saved_code
        
        context.user_data.clear()
        if saved_code:
            context.user_data["access_code"] = saved_code
            
        await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
        
    else:
        await update.message.reply_text("Нет активных операций для отмены", reply_markup=ReplyKeyboardRemove())

async def handle_text_message(update, context):
    if not context.user_data.get("access_code"):
        await update.message.reply_text(
            "**Сначала необходимо придумать код**\n\n"
            "Используйте /start для ввода кода.",
            parse_mode='Markdown'
        )
        return
    
    text = update.message.text
    if text == '🚪 Выйти из режима':
        await cancel_command(update, context)
        
    else:
        if len(text.strip())>=20 and not context.user_data.get("access_code"):
            await update.message.reply_text(
                "**Для ввода кода используйте команду /start**",
                parse_mode='Markdown'
            )
        elif text in ["📤 Загрузить", "📂 Просмотреть"]:
            return
        else:
            await update.message.reply_text("Используйте команды из меню или /menu")

async def cancel_code_input(update, context):
    await update.message.reply_text(
        "**Ввод кода отменен.**\n\n"
        "Без кода доступа функциональность бота ограничена.\n"
        "Используйте /start чтобы попробовать снова.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def setup_bot(token):
    application = Application.builder().token(token).build()
    
    start_conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_code_input)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_code_input)]
    )
    
    application.add_handler(start_conversation)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    upload_manager = UploadFileManager(cancel_command, menu_command)
    show_manager = ShowFileManager(cancel_command)
    
    application.add_handler(upload_manager.get_conversation_handler())
    application.add_handler(show_manager.get_conversation_handler())
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    return application

def main():
    application = setup_bot(BOT_TOKEN)
    application.run_polling()

if __name__ == "__main__":
    main()