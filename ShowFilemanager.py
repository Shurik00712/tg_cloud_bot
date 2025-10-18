import os
import logging
from cryptographer import decrypt_file_rust_style
from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ShowFileManager:
    def __init__(self):
        self.CHOOSE_CAT, self.CHOOSE, self.ACTION, self.RENAME, self.CONFIRM = range(3, 8)
    
    def get_conversation_handler(self, cancel_func):
        return ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^Просмотреть файлы$"), self.start_show)
            ],
            states={
                self.CHOOSE_CAT: [
                    CallbackQueryHandler(self.choose_cat)
                ],
                self.CHOOSE: [
                    CallbackQueryHandler(self.choose_file)
                ],
                self.ACTION: [CallbackQueryHandler(self.take_action)],
                self.RENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.rename)],
                self.CONFIRM: [CallbackQueryHandler(self.confirm)]
            },
            fallbacks=[CommandHandler("cancel", cancel_func)]
        )
    
    async def start_show(self, update, context):
        context.user_data["curr"] = "show"
        context.user_data.clear()
        await self.show_cat(update.message, context)
        return self.CHOOSE_CAT
    
    async def show_cat(self, message, context):
        keyboard = [
            [InlineKeyboardButton("аудио", callback_data='audio')],
            [InlineKeyboardButton("документы", callback_data='documents')],
            [InlineKeyboardButton("фотографии", callback_data='photos')],
            [InlineKeyboardButton("голосовые", callback_data='voice')],
            [InlineKeyboardButton("видео", callback_data='videos')],
            [InlineKeyboardButton("другое", callback_data='other')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            "Выберите категорию:",
            reply_markup=reply_markup
        )
    
    async def choose_cat(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.message.delete()
        context.user_data["cat"] = query.data
        
        # Проверяем есть ли файлы в категории
        user = update.effective_user
        cat = context.user_data["cat"]
        try:
            files = os.listdir(f"users/{user.id}/{cat}")
            context.user_data["path_to_show"] = f"users/{user.id}/{cat}"
        except FileNotFoundError:
            await query.message.reply_text("Вы ещё не начали загрузку файлов")
            return ConversationHandler.END
        
        if not files:
            # Если файлов нет, сразу показываем категории снова
            await query.message.reply_text("В этой категории нет файлов")
            await self.show_cat(query.message, context)
            return self.CHOOSE_CAT
        
        # Если файлы есть, показываем их
        await self.show_files_list(query.message, files)
        return self.CHOOSE
    
    async def show_files_list(self, message, files):
        keyboard = []
        for file in files:
            file = file.rsplit(".encrypted", 1)[0]
            print(file)
            keyboard.append([InlineKeyboardButton(file, callback_data=file)])
        keyboard.append([InlineKeyboardButton("К категориям", callback_data='back_to_cat')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            "Файлы:",
            reply_markup=reply_markup
        )
    
    async def choose_file(self, update, context):
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_cat":
            await query.message.delete()
            await self.show_cat(query.message, context)
            return self.CHOOSE_CAT
        
        filename = query.data
        context.user_data["selected_file"] = filename
        context.user_data["full_path"] = f"{context.user_data['path_to_show']}/{filename}"
        
        try:
            await self.send_file(update, context, query.message, filename, context.user_data["cat"])
            
            await self.show_actions_keyboard(query.message)
            return self.ACTION
            
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await query.message.reply_text("Не получилось отправить файл")
            return ConversationHandler.END
    
    async def send_file(self, update, context, message, filename, cat):
        full_path = context.user_data["full_path"]
        encrypted_path = full_path + ".encrypted"
        
        decrypt_file_rust_style(encrypted_path, full_path, update.effective_user.id)
        
        with open(full_path, 'rb') as file:
            if cat == 'photos':
                await message.reply_photo(photo=file, caption=filename)
            elif cat == 'videos':
                await message.reply_video(video=file, caption=filename)
            elif cat in ['audio', 'voice']:
                await message.reply_audio(audio=file, caption=filename)
            else:
                await message.reply_document(document=file, caption=filename)
        
        os.remove(full_path)
    
    async def show_actions_keyboard(self, message):
        keyboard = [
            [InlineKeyboardButton("Удалить", callback_data='delete')],
            [InlineKeyboardButton("Переименовать", callback_data='rename')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def take_action(self, update, context):
        query = update.callback_query
        await query.answer()
        
        if query.data == "delete":
            keyboard = [
                [InlineKeyboardButton("Да, удалить", callback_data='confirm_delete')],
                [InlineKeyboardButton("Отмена", callback_data='cancel_action')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.delete()
            await query.message.reply_text(
                "Вы уверены, что хотите удалить файл?",
                reply_markup=reply_markup
            )
            return self.CONFIRM
            
        elif query.data == "rename":
            await query.message.reply_text("Введите новое имя файла (без расширения):")
            await query.message.delete()
            return self.RENAME
    
    async def rename(self, update, context):
        new_name = update.message.text
        old_full_path = context.user_data["full_path"]
        cat = context.user_data["cat"]
        
        try:
            old_filename = context.user_data["selected_file"]
            if '.' in old_filename:
                extension = '.' + old_filename.split('.')[-1]
            else:
                extension = ''
            
            new_full_path = f"{context.user_data['path_to_show']}/{new_name}{extension}"
            old_encrypted_path = old_full_path + ".encrypted"
            new_encrypted_path = new_full_path + ".encrypted"
            
            if os.path.exists(old_encrypted_path):
                os.rename(old_encrypted_path, new_encrypted_path)
                await update.message.reply_text(f"Файл переименован в: {new_name}{extension}")
            else:
                await update.message.reply_text("Ошибка: файл не найден")
                
        except Exception as e:
            logger.error(f"Ошибка при переименовании: {e}")
            await update.message.reply_text("Ошибка при переименовании файла")
        
        return ConversationHandler.END
    
    async def confirm(self, update, context):
        query = update.callback_query
        await query.answer()
        
        if query.data == "confirm_delete":
            try:
                encrypted_path = context.user_data["full_path"] + ".encrypted"
                if os.path.exists(encrypted_path):
                    os.remove(encrypted_path)
                    await query.message.reply_text("Файл удален")
                else:
                    await query.message.reply_text("Файл не найден")
                    
            except Exception as e:
                logger.error(f"Ошибка при удалении: {e}")
                await query.message.reply_text("Ошибка при удалении файла")
                
        elif query.data == "cancel_action":
            await query.message.reply_text("Действие отменено")
        await query.message.delete()
        
        return ConversationHandler.END