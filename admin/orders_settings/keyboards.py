from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from common.lang_dicts import BUTTONS, TEXTS
from common.keyboards import build_keyboard, build_back_button, build_back_to_home_page_button
from common.common import escape_html, format_float, get_status_emoji
import models

ORDERS_PER_PAGE = 15  # Number of orders per page


def build_orders_settings_keyboard(lang: models.Language):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["charging_balance_orders"],
                callback_data="admin_charging_balance_orders",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["purchase_orders"],
                callback_data="admin_purchase_orders",
            ),
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("api_purchase_orders", "Instant Purchase Orders ⚡"),
                callback_data="admin_api_purchase_orders",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang]["request_charging_order"],
                callback_data="request_charging_order",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang]["request_purchase_order"],
                callback_data="request_purchase_order",
            ),
        ],
    ]
    return keyboard


def build_order_status_keyboard(
    lang: models.Language,
    current_status: models.ChargingOrderStatus = None,
    order_type: str = "charging",
):
    """Build keyboard for selecting order status"""
    keyboard = []
    
    if order_type == "charging":
        statuses = models.ChargingOrderStatus
    else:
        statuses = models.PurchaseOrderStatus
    
    for status in statuses:
        status_emoji = get_status_emoji(status)
        status_text = TEXTS[lang].get(f"order_status_{status.value}", status.value)
        is_selected = status == current_status
        button_text = f"{'🟢' if is_selected else '🔴'} {status_text} {status_emoji}"
        callback_data = f"set_order_status_{order_type}_{status.value}"
        
        keyboard.append(
            [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
        )
    
    return keyboard


def build_order_actions_keyboard(
    lang: models.Language,
    order_id: int,
    order_type: str,
):
    """Build keyboard with actions for an order"""
    keyboard = []
    
    # First row: Change Status and Add Notes
    first_row = [
        InlineKeyboardButton(
            text=BUTTONS[lang].get("change_status", "Change Status"),
            callback_data=f"change_status_{order_type}_{order_id}",
        ),
        InlineKeyboardButton(
            text=BUTTONS[lang].get("add_notes", "Add Notes"),
            callback_data=f"add_notes_{order_type}_{order_id}",
        ),
    ]
    keyboard.append(first_row)
    
    # Second row: Edit Amount (only for charging orders)
    if order_type == "charging":
        keyboard.append([
            InlineKeyboardButton(
                text=BUTTONS[lang].get("edit_amount", "Edit Amount"),
                callback_data=f"edit_amount_{order_type}_{order_id}",
            ),
        ])
    
    return keyboard


def build_orders_list_keyboard(
    orders: list,
    lang: models.Language,
    page: int,
    total_pages: int,
    callback_prefix: str,  # e.g., "admin_view_charge_order_", "view_api_purchase_order_"
    back_callback: str,  # e.g., "back_to_orders_settings"
    is_admin: bool = True,
) -> InlineKeyboardMarkup:
    """Build keyboard for orders list with pagination"""
    keyboard = []
    
    # Add order buttons
    for order in orders:
        if hasattr(order, 'amount'):  # ChargingBalanceOrder
            order_text = f"#{order.id} - {format_float(order.amount)}"
            status_emoji = get_status_emoji(order.status)
            status_text = TEXTS[lang].get(
                f"order_status_{order.status.value}", order.status.value
            )
            if is_admin:
                order_text += f" - {status_text} {status_emoji}"
        elif hasattr(order, 'item'):  # PurchaseOrder
            item_name = order.item.name if order.item else "N/A"
            order_text = f"#{order.id} - {escape_html(item_name[:15])}"
            status_emoji = get_status_emoji(order.status)
            status_text = TEXTS[lang].get(
                f"order_status_{order.status.value}", order.status.value
            )
            if is_admin:
                order_text += f" - {status_text} {status_emoji}"
        else:  # ApiPurchaseOrder
            game_name = (
                order.api_game.get_display_name(lang) if order.api_game else "N/A"
            )
            status_emoji = get_status_emoji(order.status)
            status_text = TEXTS[lang].get(
                f"api_order_status_{order.status.value}", order.status.value
            )
            order_text = f"#{order.id} - {escape_html(game_name[:15])} - {status_text} {status_emoji}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=order_text,
                callback_data=f"{callback_prefix}{order.id}",
            )
        ])
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        # Create pagination callback prefix by replacing the view prefix
        pagination_prefix = callback_prefix.replace("view_", "page_").replace("admin_view_", "admin_page_")
        
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
    keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=is_admin)[0])
    
    return InlineKeyboardMarkup(keyboard)
