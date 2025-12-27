from telegram import InlineKeyboardButton
from common.lang_dicts import BUTTONS, TEXTS
import models


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
        status_text = TEXTS[lang].get(f"order_status_{status.value}", status.value)
        is_selected = status == current_status
        button_text = f"{'🟢' if is_selected else '🔴'} {status_text}"
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
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("change_status", "Change Status"),
                callback_data=f"change_status_{order_type}_{order_id}",
            ),
            InlineKeyboardButton(
                text=BUTTONS[lang].get("add_notes", "Add Notes"),
                callback_data=f"add_notes_{order_type}_{order_id}",
            ),
        ],
    ]
    return keyboard

