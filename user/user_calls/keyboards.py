from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS
import models


def build_purchase_order_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["purchase_order"],
                callback_data="purchase_order",
            ),
        ],
    ]
    return keyboard

