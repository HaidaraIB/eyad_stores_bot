from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS
import models


def build_settings_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["profile"],
                callback_data="user_profile",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["lang"],
                callback_data="change_lang",
            )
        ]
    ]
    return keyboard


def build_profile_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["charge_balance"],
                callback_data="charge_balance",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["my_orders"],
                callback_data="my_orders",
            )
        ]
    ]
    return keyboard


def build_order_type_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["charging_balance_orders"],
                callback_data="charging_balance_orders",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["purchase_orders"],
                callback_data="purchase_orders",
            )
        ]
    ]
    return keyboard