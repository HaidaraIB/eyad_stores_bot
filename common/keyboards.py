from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat,
    KeyboardButtonRequestUsers,
)
from custom_filters import HasPermission
from common.lang_dicts import BUTTONS
from Config import Config
import models


def build_user_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["purchase_order"],
                callback_data="purchase_order",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["instant_purchase"],
                callback_data="instant_purchase",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["settings"],
                callback_data="user_settings",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_admin_keyboard(
    lang: models.Language = models.Language.ARABIC, user_id: int = None
):
    keyboard = []

    if user_id and user_id == Config.OWNER_ID:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["admin_settings"],
                    callback_data="admin_settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["manage_users_settings"],
                    callback_data="manage_users_settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["force_join_chats_settings"],
                    callback_data="force_join_chats_settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["games_settings"],
                    callback_data="games_settings",
                ),
                InlineKeyboardButton(
                    text=BUTTONS[lang]["items_settings"],
                    callback_data="items_settings",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang].get(
                        "filter_api_games_settings", "Filter API Games 🔍"
                    ),
                    callback_data="filter_api_games_settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["payment_methods_settings"],
                    callback_data="payment_methods_settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["orders_settings"],
                    callback_data="orders_settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["ban_unban"],
                    callback_data="ban_unban",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["hide_ids_keyboard"],
                    callback_data="hide_ids_keyboard",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang]["broadcast"],
                    callback_data="broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("general_settings", "General Settings ⚙️"),
                    callback_data="general_settings",
                )
            ],
        ]

    elif user_id:
        if HasPermission.check(user_id, models.Permission.MANAGE_FORCE_JOIN):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["force_join_chats_settings"],
                        callback_data="force_join_chats_settings",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.MANAGE_USERS):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["manage_users_settings"],
                        callback_data="manage_users_settings",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.BAN_USERS):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["ban_unban"],
                        callback_data="ban_unban",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.VIEW_IDS):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["hide_ids_keyboard"],
                        callback_data="hide_ids_keyboard",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.BROADCAST):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["broadcast"],
                        callback_data="broadcast",
                    )
                ]
            )

        if HasPermission.check(
            user_id, models.Permission.MANAGE_GAMES
        ) or HasPermission.check(user_id, models.Permission.MANAGE_ITEMS):
            row = []
            if HasPermission.check(user_id, models.Permission.MANAGE_GAMES):
                row.append(
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["games_settings"],
                        callback_data="games_settings",
                    )
                )
            if HasPermission.check(user_id, models.Permission.MANAGE_ITEMS):
                row.append(
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["items_settings"],
                        callback_data="items_settings",
                    )
                )
            keyboard.append(row)

        if HasPermission.check(user_id, models.Permission.MANAGE_PAYMENT_METHODS):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["payment_methods_settings"],
                        callback_data="payment_methods_settings",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.MANAGE_ORDERS):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang]["orders_settings"],
                        callback_data="orders_settings",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.MANAGE_GENERAL_SETTINGS):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang].get(
                            "general_settings", "General Settings ⚙️"
                        ),
                        callback_data="general_settings",
                    )
                ]
            )

        if HasPermission.check(user_id, models.Permission.FILTER_API_GAMES):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=BUTTONS[lang].get(
                            "filter_api_games_settings", "Filter API Games 🔍"
                        ),
                        callback_data="filter_api_games_settings",
                    )
                ]
            )

    return InlineKeyboardMarkup(keyboard)


def build_back_to_home_page_button(
    lang: models.Language = models.Language.ARABIC, is_admin: bool = True
):
    button = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["back_to_home_page"],
                callback_data=f"back_to_{'admin' if is_admin else 'user'}_home_page",
            )
        ],
    ]
    return button


def build_back_button(data: str, lang: models.Language = models.Language.ARABIC):
    return [
        InlineKeyboardButton(
            text=BUTTONS[lang]["back_button"],
            callback_data=data,
        ),
    ]


def build_skip_button(data: str, lang: models.Language = models.Language.ARABIC):
    return [
        InlineKeyboardButton(
            text=BUTTONS[lang]["skip_button"],
            callback_data=data,
        ),
    ]


def build_request_buttons(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            KeyboardButton(
                text=BUTTONS[lang]["user"],
                request_users=KeyboardButtonRequestUsers(
                    request_id=0, user_is_bot=False
                ),
            ),
            KeyboardButton(
                text=BUTTONS[lang]["channel"],
                request_chat=KeyboardButtonRequestChat(
                    request_id=1, chat_is_channel=True
                ),
            ),
        ],
        [
            KeyboardButton(
                text=BUTTONS[lang]["group"],
                request_chat=KeyboardButtonRequestChat(
                    request_id=2, chat_is_channel=False
                ),
            ),
            KeyboardButton(
                text=BUTTONS[lang]["bot"],
                request_users=KeyboardButtonRequestUsers(
                    request_id=3, user_is_bot=True
                ),
            ),
        ],
    ]
    return keyboard


def build_keyboard(columns: int, texts: list, buttons_data: list):
    if len(texts) != len(buttons_data):
        raise ValueError("The length of 'texts' and 'buttons_data' must be the same.")

    keyboard = []
    for i in range(0, len(buttons_data), columns):
        row = [
            InlineKeyboardButton(
                text=texts[i + j],
                callback_data=buttons_data[i + j],
            )
            for j in range(columns)
            if i + j < len(buttons_data)
        ]
        if row:  # Only append non-empty rows
            keyboard.append(row)
    return keyboard
