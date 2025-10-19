import os
import logging
import datetime
from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from cryptographer import encrypt_file

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class UploadFileManager:
    def __init__(self, cancel_func, menu_func):
        self.UPLOAD_FILE, self.DECISION, self.CONFIRM = range(3)
        self.cancel = cancel_func
        self.menu_func = menu_func
    
    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^📤 Загрузить$"), self.handle_message)
            ],
            states={
                self.UPLOAD_FILE: [
                    MessageHandler(filters.TEXT | filters.Document.ALL | filters.PHOTO | 
                                  filters.VOICE | filters.VIDEO, self.handle_file_data)
                ],
                self.DECISION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_file_decision)
                ],
                self.CONFIRM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_file)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CommandHandler("menu", self.menu_wrapper(self.menu_func))
            ]
        )
    
    def menu_wrapper(self, menu_func):
        async def wrapper(update, context):
            saved_code = context.user_data.get("access_code")
            context.user_data.clear()
            if saved_code:
                context.user_data["access_code"] = saved_code
            await update.message.reply_text("Возврат в главное меню", reply_markup=ReplyKeyboardRemove())
            
            return await menu_func(update, context)
        return wrapper
    
    async def handle_message(self, update, context):
        saved_code = context.user_data.get("access_code")
        context.user_data.clear()
        if saved_code:
            context.user_data["access_code"] = saved_code
        context.user_data["curr"] = "upload"
        await update.message.reply_text(f"Загрузите файл", reply_markup=ReplyKeyboardRemove())
        return self.UPLOAD_FILE
    
    async def get_file_data_type(self, update, context):
        file_obj = None
        file_data = None
        
        if update.message.text:
            return (None, None)
        
        file_handlers = {
            'document': (lambda: update.message.document, '.docx'),
            'photo': (lambda: update.message.photo[-1], '.jpg'),
            'video': (lambda: update.message.video, '.mp4'),
            'audio': (lambda: update.message.audio, '.mp3'),
            'voice': (lambda: update.message.voice, '.ogg'),
            'video_note': (lambda: update.message.video_note, '.mp4'),
            'sticker': (lambda: update.message.sticker, None),
            'animation': (lambda: update.message.animation, '.gif')
        }
        
        for file_type, (file_getter, default_ext) in file_handlers.items():
            file_data = file_getter()
            if file_data:
                file_obj = await file_data.get_file()
                
                if file_type == 'sticker':
                    if file_data.is_animated:
                        context.user_data["file_ext"] = ".tgs"
                    elif file_data.is_video:
                        context.user_data["file_ext"] = ".webm"
                    else:
                        context.user_data["file_ext"] = ".webp"
                else:
                    original_ext = os.path.splitext(getattr(file_data, 'file_name', ''))[1].lower()
                    context.user_data["file_ext"] = original_ext if original_ext else default_ext
                
                break
        
        return (file_data, file_obj)
        
    async def handle_file_data(self, update, context):
        if not context.user_data.get("curr"):
            return ConversationHandler.END
        user = update.effective_user
        file_data, file_obj = await self.get_file_data_type(update, context)
        
        if not file_data and update.message.text == '📤 Загрузить':
            await update.message.reply_text("Загрузка уже начата", reply_markup=ReplyKeyboardRemove())
            return self.UPLOAD_FILE
        elif not file_data and update.message.text != '📤 Загрузить':
            await update.message.reply_text("Нужно отправить файл, а не текст", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        
        if not file_data or not file_obj:
            await update.message.reply_text("Не удалось обработать файл", reply_markup=ReplyKeyboardRemove())
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
        
        save_path = f"users/{user.id}/{folder}/"
        os.makedirs(save_path, exist_ok=True)
        
        context.user_data["file_file"] = file_obj
        context.user_data["file_path"] = save_path
        context.user_data["file_id"] = file_obj.file_id
        context.user_data["file_name"] = update.message.caption
        
        keyboard = [["добавить имя файла"], ["отменить загрузку"], ["продолжить"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
        
        return self.DECISION
    
    async def handle_file_decision(self, update, context):
        context.user_data["action_file"] = ""
        
        text = update.message.text
        if text == "добавить имя файла":
            await update.message.reply_text("Введите имя:", reply_markup=ReplyKeyboardRemove())
            context.user_data["action_file"] = "waiting_for_filename"
            return self.CONFIRM
        elif text == "отменить загрузку":
            return await self.cancel(update, context)
        elif text == "продолжить":
            context.user_data["action_file"] = "use_id_or_name"
            return await self.confirm_file(update, context)
        
        return self.DECISION
    
    async def confirm_file(self, update, context):
        filename = ""
        if context.user_data["action_file"] == "waiting_for_filename":
            filename = update.message.text
        elif context.user_data["action_file"] == "use_id_or_name":
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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
            
            try:
                path = f"{context.user_data['file_path']}{filename}{context.user_data['file_ext']}"
                await context.user_data['file_file'].download_to_drive(path)
                encrypt_file(path, path+".encrypted", context.user_data["access_code"])
                await update.message.reply_text("Файл успешно сохранен", reply_markup=ReplyKeyboardRemove())
            except Exception as e:
                logger.error(f"Ошибка при сохранении файла: {e}")
                await update.message.reply_text("Не получилось сохранить файл", reply_markup=ReplyKeyboardRemove())
        
        saved_code = context.user_data.get("access_code")
        context.user_data.clear()
        if saved_code:
            context.user_data["access_code"] = saved_code
        
        return ConversationHandler.END