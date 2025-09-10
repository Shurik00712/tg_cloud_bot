import logging
import os
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
async def start(update, context):
    user = update.effective_user
    context.user_data["can_upload"] = False
    text = f"""Привет, {user.first_name}!
    Я бот CLOUDATA!
    создатель SANYOK007
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
async def handle_voice(update, context):
    voice = update.message.voice()
    file = await voice.get_file()
    
    await file.download_to_drive(f"data/voice/{file.file_id}.ogg")
    
    await update.message.reply_text(
        f"Голосовое сообщение получено! "
        f"Длительность: {voice.duration} сек"
    )
async def handle_photo(update, context):
    # Бот получает фото в разных размерах, берем самое большое
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    # Скачиваем фото
    await file.download_to_drive(f"data/photos/{file.file_id}.jpg")
    
    await update.message.reply_text("Фото получено!")

async def handle_document(update, context):
    document = update.message.document
    file = await document.get_file()
    
    # Скачиваем файл
    await file.download_to_drive(f"data/downloads/{document.file_name}")
    
    await update.message.reply_text(
        f"Файл {document.file_name} получен! "
        f"Размер: {document.file_size} байт"
    )
async def handle_video(update, context):
    video = update.message.video
    file = await video.get_file()
    
    await file.download_to_drive(f"data/videos/{video.file_name or file.file_id}.mp4")
    
    await update.message.reply_text("Видео получено!")
    
    #async def handle_file()
async def handle_file(update, context):
    file_info = None
    file_obj = None
    filename = ""
    file_size = 0


    user = update.effective_user

    os.makedirs(f"users/{user.id}/audio", exist_ok=True)
    os.makedirs(f"users/{user.id}/documents", exist_ok=True)
    os.makedirs(f"users/{user.id}/other", exist_ok=True)
    os.makedirs(f"users/{user.id}/photos", exist_ok=True)
    os.makedirs(f"users/{user.id}/videos", exist_ok=True)
    os.makedirs(f"users/{user.id}/voice", exist_ok=True)
    
    # Определяем тип файла и получаем объект
    # if update.message.text=='Загрузить данные':
    #     print("Грузи")
    #     context.user_data['can_upload'] = True
    #     return
    
    if update.message.document:
        file_info = update.message.document
        file_obj = await file_info.get_file()
        filename = file_info.file_name or f"document_{file_info.file_id}"
        file_size = file_info.file_size
        
    elif update.message.photo:
        file_info = update.message.photo[-1]
        file_obj = await file_info.get_file()
        filename = f"photo_{file_info.file_id}.jpg"
        file_size = file_info.file_size
        
    elif update.message.video:
        file_info = update.message.video
        file_obj = await file_info.get_file()
        filename = file_info.file_name or f"video_{file_info.file_id}.mp4"
        file_size = file_info.file_size
        
    elif update.message.audio:
        file_info = update.message.audio
        file_obj = await file_info.get_file()
        filename = file_info.file_name or f"audio_{file_info.file_id}.mp3"
        file_size = file_info.file_size
        
    elif update.message.voice:
        file_info = update.message.voice
        file_obj = await file_info.get_file()
        filename = f"voice_{file_info.file_id}.ogg"
        file_size = file_info.file_size
        
    elif update.message.video_note:
        file_info = update.message.video_note
        file_obj = await file_info.get_file()
        filename = f"video_note_{file_info.file_id}.mp4"
        file_size = file_info.file_size
        
    elif update.message.sticker:
        file_info = update.message.sticker
        file_obj = await file_info.get_file()
        # Определяем расширение стикера
        if file_info.is_animated:
            extension = "tgs"
        elif file_info.is_video:
            extension = "webm"
        else:
            extension = "webp"
        filename = f"sticker_{file_info.file_id}.{extension}"
        file_size = file_info.file_size
        
    elif update.message.animation:
        file_info = update.message.animation
        file_obj = await file_info.get_file()
        filename = file_info.file_name or f"animation_{file_info.file_id}.mp4"
        file_size = file_info.file_size
    if not file_info or not file_obj:
        await update.message.reply_text("❌ Не удалось обработать файл")
        return
    file_extension = os.path.splitext(filename)[1].lower() if '.' in filename else ''
    if file_extension in ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        folder = "documents"
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        folder = "photos"
    elif file_extension in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        folder = "videos"
    elif file_extension in ['.mp3', '.wav', '.ogg', '.flac']:
        folder = "videos"
    else:
        folder = "other"
        
        # Полный путь для сохранения
    print("ok")
    save_path = f"users/{user.id}/{folder}/{filename}"
        
        # Скачиваем файл
    try:
        # Скачиваем файл
        await update.message.reply_text(f"📥 Скачиваю {filename}...")
        await file_obj.download_to_drive(save_path)
        await update.message.reply_text(
            f"✅ Файл {filename} успешно сохранен в папку {folder}!\n"
            f"Размер: {file_size} байт"
        )
        context.user_data['can_upload'] = False
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        await update.message.reply_text("❌ Произошла ошибка при сохранении файла.")
async def handle_message(update, context):
    text = update.message.text
    if text == 'Загрузить данные':
        user = update.effective_user
        context.user_data['can_upload'] = True
        await update.message.reply_text(
        f"Грузи, {user.first_name} "
    )
def setup_bot(token):
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL | filters.PHOTO | filters.VOICE | filters.VIDEO, handle_file))
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