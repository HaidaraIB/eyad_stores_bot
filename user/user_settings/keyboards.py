from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from common.lang_dicts import BUTTONS, TEXTS
from common.keyboards import build_back_button, build_back_to_home_page_button
from common.common import escape_html, format_float
import models

ORDERS_PER_PAGE = 10  # Number of orders per page for users


def build_settings_keyboard(lang: models.Language):
    keyboard = [
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
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("api_purchase_orders", "API Purchase Orders ⚡"),
                callback_data="api_purchase_orders",
            )
        ]
    ]
    return keyboard


def build_user_orders_list_keyboard(
    orders: list,
    lang: models.Language,
    page: int,
    total_pages: int,
    callback_prefix: str,  # e.g., "view_charge_order_", "view_api_purchase_order_"
    back_callback: str,  # e.g., "back_to_my_orders"
) -> InlineKeyboardMarkup:
    """Build keyboard for user orders list with pagination"""
    from telegram import InlineKeyboardMarkup
    from common.keyboards import build_back_button, build_back_to_home_page_button
    from common.lang_dicts import TEXTS
    from common.common import escape_html, format_float
    
    keyboard = []
    
    # Add order buttons
    for order in orders:
        if hasattr(order, 'amount'):  # ChargingBalanceOrder
            order_text = f"#{order.id} - {format_float(order.amount)}"
        elif hasattr(order, 'item'):  # PurchaseOrder
            item_name = order.item.name if order.item else "N/A"
            order_text = f"#{order.id} - {escape_html(item_name[:15])}"
        else:  # ApiPurchaseOrder
            game_name = (
                order.api_game.get_display_name(lang) if order.api_game else "N/A"
            )
            status_text = TEXTS[lang].get(
                f"api_order_status_{order.status.value}", order.status.value
            )
            order_text = f"#{order.id} - {escape_html(game_name[:15])} - {status_text}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=order_text,
                callback_data=f"{callback_prefix}{order.id}",
            )
        ])
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        # Create pagination callback prefix
        pagination_prefix = callback_prefix.replace("view_", "page_")
        
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️ " + BUTTONS[lang].get("back_button", "Back"),
                    callback_data=f"{pagination_prefix}{page - 1}",
                )
            )
        
        # Page indicator (non-clickable info)
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="page_info",
            )
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("next_button", "Next") + " ▶️",
                    callback_data=f"{pagination_prefix}{page + 1}",
                )
            )
        
        if pagination_row:
            keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append(build_back_button(back_callback, lang=lang))
    keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
    
    return InlineKeyboardMarkup(keyboard)