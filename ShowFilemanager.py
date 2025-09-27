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
        self.CHOOSE_CAT, self.CHOOSE, self.CONFIRM = range(3, 6)
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
                ]
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
            "Выберите опцию:",
            reply_markup=reply_markup
        )
    async def choose_cat(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.message.delete()
        context.user_data["cat"] = query.data
        await self.show_files(update, context, query)
        return self.CHOOSE
    async def show_files(self, update, context, query):
        keyboard = []
        user = update.effective_user
        cat = context.user_data["cat"]
        try:
            files = os.listdir(f"users/{user.id}/{cat}")
            context.user_data["path_to_show"] = f"users/{user.id}/{cat}"
        except FileNotFoundError:
            await query.message.reply_text("Вы ещё не начали загрузку файлов")
            return ConversationHandler.END
        if not files:
            await query.message.reply_text("Файлы не найдены")
            await self.show_cat(update.callback_query.message, context)
        for file in files:
            file = file.rsplit(".encrypted", 1)[0]
            keyboard.append([InlineKeyboardButton(file, callback_data=file)])
        keyboard.append([InlineKeyboardButton("К категориям", callback_data='back_to_cat')])
        reply_markup = InlineKeyboardMarkup(keyboard)
    
        await query.message.reply_text(
            "Файлы:",
            reply_markup=reply_markup
        )
    async def choose_file(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.message.delete()
        if query.data == "back_to_cat":
            await self.show_cat(update.callback_query.message, context)
            return self.CHOOSE_CAT
        filename = query.data
        message = query.message
        cat = context.user_data["cat"]
        try:
            await self.send_file(context, message, filename, cat)
        except:
            await message.reply_text("Не получилось отправить файл")
            return ConversationHandler.END
    async def send_file(self, context, query, filename, cat):
        decrypt_file_rust_style(context.user_data["path_to_show"]+"/"+filename+".encrypted", context.user_data["path_to_show"]+"/"+filename, 100)
        with open(context.user_data["path_to_show"]+"/"+filename, 'rb') as file:
            if cat == 'photos':
                await query.reply_photo(photo=file, caption=filename)
            elif cat == 'videos':
                await query.reply_video(video=file, caption=filename)
            elif cat in ['audio', 'voice']:
                await query.reply_audio(audio=file, caption=filename)
            else:
                await query.reply_document(document=file, caption=filename)
        return ConversationHandler.END
    
        