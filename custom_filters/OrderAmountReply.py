from telegram import Update
from telegram.ext.filters import BaseFilter
import models


class OrderAmountReplyFilter(BaseFilter):
    """فلتر للتحقق من أن الرسالة هي رد على رسالة طلب تحتوي على زر Edit Amount"""
    
    def filter(self, update: Update):
        # التحقق من أن الرسالة موجودة وهي رد على رسالة أخرى
        if not update.message or not update.message.reply_to_message:
            return False
        
        # التحقق من أن الرسالة نصية
        if not update.message.text:
            return False
        
        # التحقق من أن المستخدم أدمن
        user_id = update.effective_user.id if update.effective_user else None
        if not user_id:
            return False
        
        with models.session_scope() as s:
            user = s.get(models.User, user_id)
            if not user or not user.is_admin:
                return False
        
        # التحقق من أن الرسالة المرد عليها تحتوي على keyboard مع زر "Edit Amount"
        replied_message = update.message.reply_to_message
        
        # التحقق من وجود keyboard في الرسالة المرد عليها
        if replied_message.reply_markup:
            keyboard = replied_message.reply_markup
            if hasattr(keyboard, 'inline_keyboard'):
                for row in keyboard.inline_keyboard:
                    for button in row:
                        callback_data = button.callback_data
                        # التحقق من وجود زر "Edit Amount" - هذا أكثر تحديداً من Add Notes
                        if callback_data and callback_data.startswith("edit_amount_"):
                            return True
        
        return False

