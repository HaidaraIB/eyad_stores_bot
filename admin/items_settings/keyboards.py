from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS, TEXTS
import models


def build_items_settings_keyboard(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["add_item"],
                callback_data="add_item",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["remove_item"],
                callback_data="remove_item",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["edit_item"],
                callback_data="edit_item",
            )
        ],
    ]
    return keyboard


def build_item_type_keyboard(
    lang: models.Language, selected_type: models.ItemType = None
):
    keyboard = []
    for item_type in models.ItemType:
        item_type_name = BUTTONS[lang].get(f"item_type_{item_type.value}")
        is_selected = item_type == selected_type
        button_text = f"{'🟢' if is_selected else '🔴'} {item_type_name}"
        callback_data = f"select_item_type_{item_type.value}"

        keyboard.append(
            [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
        )

    return keyboard


def build_edit_item_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_item_name"],
                callback_data="edit_item_name",
            ),
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_item_type"],
                callback_data="edit_item_type",
            ),
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_item_price"],
                callback_data="edit_item_price",
            ),
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_item_stock"],
                callback_data="edit_item_stock",
            ),
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_item_description"],
                callback_data="edit_item_description",
            )
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["toggle_item_status"],
                callback_data="toggle_item_status",
            )
        ],
    ]
    return keyboard
