from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS
import models


def build_manage_users_settings_keyboard(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["export_users_to_excel"],
                callback_data="export_users_to_excel",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("edit_user_balance", "تعديل رصيد المستخدم"),
                callback_data="edit_user_balance",
            )
        ],
    ]
    return keyboard


def build_user_balance_actions_keyboard(lang: models.Language, user_id: int):
    """Build keyboard with balance action options for a user"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("add_deduct_balance", "إضافة/خصم مبلغ"),
                callback_data=f"balance_action_add_deduct_{user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("set_new_balance", "تعيين رصيد جديد"),
                callback_data=f"balance_action_set_{user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("zero_balance", "تصفير الرصيد"),
                callback_data=f"balance_action_zero_{user_id}",
            )
        ],
    ]
    return keyboard

