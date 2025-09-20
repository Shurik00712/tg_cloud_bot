import os
import logging
from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
class UploadFileManager:
    def __init__(self):
        self.UPLOAD_FILE, self.DECISION, self.CONFIRM = range(3)
    
    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
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
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
    
    async def handle_message(self, update, context):
        text = update.message.text
        if text == 'Загрузить данные':
            user = update.effective_user
            await update.message.reply_text(f"Грузи, {user.first_name}", reply_markup=ReplyKeyboardRemove())
            return self.UPLOAD_FILE
        return ConversationHandler.END
    
    async def handle_file_data(self, update, context):
        user = update.effective_user
        file_obj = None
        
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
        
        for file_type, (file_data, default_ext) in file_handlers.items():
            file_data = file_data()
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
        
        if not file_data and update.message.text != 'Загрузить данные':
            await update.message.reply_text("Нужно отправить файл, а не текст", reply_markup=ReplyKeyboardRemove())
            return self.UPLOAD_FILE
        elif not file_data or not file_obj:
            await update.message.reply_text("❌ Не удалось обработать файл", reply_markup=ReplyKeyboardRemove())
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
        
        # if update.message.photo:
        #     file_obj = file_obj[-1]
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
            await update.message.reply_text("Введите имя:")
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
            filename = context.user_data["file_name"] or context.user_data["file_id"]
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
                await context.user_data['file_file'].download_to_drive(
                    f"{context.user_data['file_path']}{filename}{context.user_data['file_ext']}"
                )
                await update.message.reply_text("Файл успешно сохранен", reply_markup=ReplyKeyboardRemove())
            except Exception as e:
                logger.error(f"Ошибка при сохранении файла: {e}")
                await update.message.reply_text("Не получилось сохранить файл", reply_markup=ReplyKeyboardRemove())
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel(self, update, context):
        if "file_file" not in context.user_data:
            text = """
            Вы ещё не начали загрузку файла"""
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("Загрузка файла отменена", reply_markup=ReplyKeyboardRemove())
            context.user_data.clear()
        return ConversationHandler.END