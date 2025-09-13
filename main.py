import logging
import os
from dotenv import load_dotenv
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
async def handle_message(update, context):
    text = update.message.text
    if text == 'Загрузить данные':
        user = update.effective_user
        await update.message.reply_text(
        f"Грузи, {user.first_name} ")
        return UPLOAD_FILE
    return ConversationHandler.END
async def handle_file_data(update, context):
    user = update.effective_user
    file_info = None
    file_obj = None
    
    file_handlers = {
        'document': (update.message.document, '.docx'),
        'photo': (update.message.photo[-1] if update.message.photo else None, '.jpg'),
        'video': (update.message.video, '.mp4'),
        'audio': (update.message.audio, '.mp3'),
        'voice': (update.message.voice, '.ogg'),
        'video_note': (update.message.video_note, '.mp4'),
        'sticker': (update.message.sticker, None),  
        'animation': (update.message.animation, '.gif')
    }
    
    for file_type, (file_data, default_ext) in file_handlers.items():
        if file_data:
            file_info = file_data
            file_obj = await file_info.get_file()
            
            if file_type == 'sticker':
                if file_info.is_animated:
                    context.user_data["file_ext"] = ".tgs"
                elif file_info.is_video:
                    context.user_data["file_ext"] = ".webm"
                else:
                    context.user_data["file_ext"] = ".webp"
            else:
                original_ext = os.path.splitext(getattr(file_info, 'file_name', ''))[1].lower()
                context.user_data["file_ext"] = original_ext if original_ext else default_ext
            
            break
    
    if not file_info or not file_obj:
        await update.message.reply_text("❌ Не удалось обработать файл")
        return ConversationHandler.END
    
    file_ext = context.user_data["file_ext"]
    folder_map = {
        'documents': ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
        'photos': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
        'videos': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
        'audio': ['.mp3', '.wav', '.ogg', '.flac']
    }
    
    folder = "other"
    for folder_name, extensions in folder_map.items():
        if file_ext in extensions:
            folder = folder_name
            break
    
    # Создаем папку и сохраняем данные
    save_path = f"users/{user.id}/{folder}/"
    os.makedirs(save_path, exist_ok=True)
    
    context.user_data["file_file"] = file_obj
    context.user_data["file_path"] = save_path
    context.user_data["file_id"] = file_info.file_id
    
    # Показываем клавиатуру с опциями
    keyboard = [["добавить имя файла"], ["отменить загрузку"], ["продолжить"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
    
    return DECISION
async def handle_file_decision(update, context):
    context.user_data["action_file"] = ""
    print(11)
    
    text = update.message.text
    if text == "добавить имя файла":
        await update.message.reply_text("Введите имя:")
        context.user_data["action_file"] = "waiting_for_filename"
        print(111)
        return CONFIRM
    elif text == "отменить загрузку":
        context.user_data.clear()
        await update.message.reply_text("Загрузка отменена", reply_markup=ReplyKeyboardRemove())
        print(222)
        return ConversationHandler.END
    elif text == "продолжить":
        context.user_data["action_file"] = "use_id"
        print(333)
        return CONFIRM
    return DECISION
async def confirm_file(update, context):
    filename = ""
    if context.user_data["action_file"] == "waiting_for_filename":
        filename = update.message.text
    elif context.user_data["action_file"] == "use_id":
        filename = context.user_data["file_id"]
    else:
        return ConversationHandler.END
    if context.user_data["action_file"] != "deny_download":
        user = update.effective_user
        os.makedirs(f"users/{user.id}/audio", exist_ok=True)
        os.makedirs(f"users/{user.id}/documents", exist_ok=True)
        os.makedirs(f"users/{user.id}/other", exist_ok=True)
        os.makedirs(f"users/{user.id}/photos", exist_ok=True)
        os.makedirs(f"users/{user.id}/videos", exist_ok=True)
        os.makedirs(f"users/{user.id}/voice", exist_ok=True)
        print(filename, context.user_data['file_ext'])
        try:
            await context.user_data['file_file'].download_to_drive(f"{context.user_data['file_path']}{filename}.{context.user_data['file_ext']}")
            await update.message.reply_text("Файл успешно сохранен", reply_markup=ReplyKeyboardRemove())
        except:
            await update.message.reply_text("Не получилось сохранить файл", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END
async def cancel(update, context):
    await update.message.reply_text("Загрузка файла отменена", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END
    #     # Скачиваем файл
    # try:
    #     # Скачиваем файл
    #     await update.message.reply_text(f"📥 Скачиваю {filename}...")
    #     await file_obj.download_to_drive(save_path)
    #     await update.message.reply_text(
    #         f"✅ Файл {filename} успешно сохранен в папку {folder}!\n"
    #         f"Размер: {file_size} байт"
    #     )
    #     context.user_data['can_upload'] = False
    # except Exception as e:
    #     logger.error(f"Ошибка при загрузке файла: {e}")
    #     await update.message.reply_text("❌ Произошла ошибка при сохранении файла.")
def setup_bot(token):
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("menu", menu_command))
    conv_handler = ConversationHandler(entry_points=
            [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            UPLOAD_FILE: [
                MessageHandler(filters.TEXT | filters.Document.ALL | filters.PHOTO | filters.VOICE | filters.VIDEO, handle_file_data)
            ],
            DECISION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_file_decision)
            ],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_file)
            ],
        }, fallbacks = [CommandHandler("cancel", cancel)])
    application.add_handler(conv_handler)
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