from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS, TEXTS
import models


def build_payment_methods_settings_keyboard(
    lang: models.Language = models.Language.ARABIC,
):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["add_payment_method"],
                callback_data="add_payment_method",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["remove_payment_method"],
                callback_data="remove_payment_method",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["edit_payment_method"],
                callback_data="edit_payment_method",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["manage_payment_addresses"],
                callback_data="manage_payment_addresses",
            )
        ],
    ]
    return keyboard


def build_payment_method_type_keyboard(
    lang: models.Language, selected_type: models.PaymentMethodType = None
):
    keyboard = []
    for payment_type in models.PaymentMethodType:
        type_name = BUTTONS[lang].get(f"payment_type_{payment_type.value}")
        is_selected = payment_type == selected_type
        button_text = f"{'🟢' if is_selected else '🔴'} {type_name}"
        callback_data = f"select_payment_type_{payment_type.value}"

        keyboard.append(
            [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
        )

    return keyboard


def build_edit_payment_method_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_payment_method_name"],
                callback_data="edit_payment_method_name",
            ),
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_payment_method_type"],
                callback_data="edit_payment_method_type",
            ),
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["edit_payment_method_description"],
                callback_data="edit_payment_method_description",
            )
        ],
        [
            InlineKeyboardButton(
                text=TEXTS[lang]["toggle_payment_method_status"],
                callback_data="toggle_payment_method_status",
            )
        ],
    ]
    return keyboard


def build_payment_addresses_keyboard(payment_method_id: int, lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["add_payment_address"],
                callback_data=f"add_payment_address_{payment_method_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["remove_payment_address"],
                callback_data=f"remove_payment_address_{payment_method_id}",
            )
        ],
    ]
    return keyboard
