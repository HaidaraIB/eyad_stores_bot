from telegram import Update
from telegram.ext.filters import BaseFilter
import models


class OrderNotesReplyFilter(BaseFilter):
    """فلتر للتحقق من أن الرسالة هي رد على رسالة طلب تنتظر ملاحظات من الأدمن"""
    
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
        
        # التحقق من أن الرسالة المرد عليها تحتوي على keyboard مع أزرار "Add Notes"
        # أو تحتوي على نص يشير إلى طلب
        replied_message = update.message.reply_to_message
        
        # التحقق من وجود keyboard في الرسالة المرد عليها
        if replied_message.reply_markup:
            keyboard = replied_message.reply_markup
            if hasattr(keyboard, 'inline_keyboard'):
                has_edit_amount = False
                has_order_buttons = False
                
                for row in keyboard.inline_keyboard:
                    for button in row:
                        callback_data = button.callback_data
                        if callback_data:
                            # إذا كان هناك زر Edit Amount، لا نعالج كملاحظات (فلتر Edit Amount أكثر تحديداً)
                            if callback_data.startswith("edit_amount_"):
                                has_edit_amount = True
                            # التحقق من وجود أزرار الطلبات
                            elif (
                                callback_data.startswith("add_notes_") or
                                callback_data.startswith("change_status_") or
                                callback_data.startswith("admin_view_charge_order_") or
                                callback_data.startswith("admin_view_purchase_order_")
                            ):
                                has_order_buttons = True
                
                # إذا كان هناك زر Edit Amount، لا نعالج كملاحظات
                if has_edit_amount:
                    return False
                
                # إذا كان هناك أزرار طلبات بدون Edit Amount، نعالج كملاحظات
                if has_order_buttons:
                    return True
        
        # التحقق من أن النص يحتوي على "Order ID" أو "Order Details" أو "order_details_text"
        # هذه النصوص موجودة فقط في رسائل الطلبات
        if replied_message.text or replied_message.caption:
            text = replied_message.text or replied_message.caption
            if text and (
                "Order ID" in text or
                "Order Details" in text or
                "order_details_text" in text or
                "رقم الطلب" in text or
                "تفاصيل الطلب" in text
            ):
                return True
        
        return False

