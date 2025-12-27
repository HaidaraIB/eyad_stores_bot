from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS
import models


def build_general_settings_keyboard(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("usd_to_sudan_rate", "USD to Sudan Rate"),
                callback_data="set_usd_to_sudan_rate",
            )
        ],
    ]
    return keyboard

