from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS, TEXTS
import models


def build_games_settings_keyboard(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["add_game"],
                callback_data="add_game",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["remove_game"],
                callback_data="remove_game",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["edit_game"],
                callback_data="edit_game",
            )
        ],
    ]
    return keyboard


def build_edit_game_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_game_name"],
                callback_data="edit_game_name",
            ),
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_game_code"],
                callback_data="edit_game_code",
            )
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_game_description"],
                callback_data="edit_game_description",
            )
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["toggle_game_status"],
                callback_data="toggle_game_status",
            )
        ],
    ]
    return keyboard
