from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS
import models


def build_admin_settings_keyboard(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["add_admin"],
                callback_data="add_admin",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["remove_admin"],
                callback_data="remove_admin",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["show_admins"],
                callback_data="show_admins",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["edit_permissions"],
                callback_data="edit_admin_permissions",
            )
        ],
    ]
    return keyboard


def build_permissions_keyboard(
    lang: models.Language,
    selected_permissions: set = None,
):
    if selected_permissions is None:
        selected_permissions = set()

    keyboard = []

    for permission in models.Permission:
        permission_name = BUTTONS[lang].get(f"permission_{permission.value}")
        is_selected = permission in selected_permissions

        button_text = f"{'🟢' if is_selected else '🔴'} {permission_name}"
        callback_data = f"toggle_permission_{permission.value}"

        keyboard.append(
            [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
        )

    return keyboard
