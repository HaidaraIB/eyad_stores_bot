from telegram import (
    Update,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from admin.orders_settings.keyboards import (
    build_orders_settings_keyboard,
    build_order_status_keyboard,
    build_order_actions_keyboard,
)
from common.keyboards import (
    build_admin_keyboard,
    build_back_to_home_page_button,
    build_back_button,
    build_keyboard,
)
from common.lang_dicts import TEXTS, get_lang
from common.back_to_home_page import back_to_admin_home_page_handler
from common.common import escape_html, format_datetime, format_float
from custom_filters import PrivateChatAndAdmin, PermissionFilter
from start import admin_command, start_command
import models

# Conversation states for adding notes
ADD_ORDER_NOTES = range(1)


async def orders_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_orders_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get("orders_settings_title", "Orders Management"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


orders_settings_handler = CallbackQueryHandler(
    orders_settings,
    "^orders_settings$|^back_to_orders_settings$",
)


async def request_charging_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            # Find oldest pending or processing charging order
            order = (
                s.query(models.ChargingBalanceOrder)
                .filter(
                    models.ChargingBalanceOrder.status.in_(
                        [
                            models.ChargingOrderStatus.PENDING,
                            models.ChargingOrderStatus.PROCESSING,
                        ]
                    )
                )
                .order_by(models.ChargingBalanceOrder.created_at.asc())
                .first()
            )

            if not order:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "no_pending_orders", "No pending or processing orders found ❗️"
                    ),
                    show_alert=True,
                )
                return

            # Display the order (same as view_charging_balance_order_admin)
            order_id = order.id
            # Send payment proof if exists
            if order.payment_proof:
                try:
                    await update.callback_query.message.reply_photo(
                        photo=order.payment_proof,
                        caption=TEXTS[lang]["payment_proof"],
                    )
                except:
                    try:
                        await update.callback_query.message.reply_document(
                            document=order.payment_proof,
                            caption=TEXTS[lang]["payment_proof"],
                        )
                    except:
                        pass
            # Use stringify method and add user info
            text = order.stringify(lang)
            text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
            text += f"\n{order.user.stringify(lang)}"

            actions_keyboard = build_order_actions_keyboard(lang, order_id, "charging")
            actions_keyboard.append(
                build_back_button("back_to_orders_settings", lang=lang)
            )
            actions_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(actions_keyboard),
            )


request_charging_order_handler = CallbackQueryHandler(
    request_charging_order,
    "^request_charging_order$",
)


async def request_purchase_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            # Find oldest pending or processing purchase order
            order = (
                s.query(models.PurchaseOrder)
                .filter(
                    models.PurchaseOrder.status.in_(
                        [
                            models.PurchaseOrderStatus.PENDING,
                            models.PurchaseOrderStatus.PROCESSING,
                        ]
                    )
                )
                .order_by(models.PurchaseOrder.created_at.asc())
                .first()
            )

            if not order:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "no_pending_orders", "No pending or processing orders found ❗️"
                    ),
                    show_alert=True,
                )
                return

            # Display the order (same as view_purchase_order_admin)
            order_id = order.id
            # Use stringify method and add user info
            text = order.stringify(lang)
            text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
            text += f"\n{order.user.stringify(lang)}"

            actions_keyboard = build_order_actions_keyboard(lang, order_id, "purchase")
            actions_keyboard.append(
                build_back_button("back_to_orders_settings", lang=lang)
            )
            actions_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(actions_keyboard),
            )


request_purchase_order_handler = CallbackQueryHandler(
    request_purchase_order,
    "^request_purchase_order$",
)


async def show_charging_balance_orders_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            orders = (
                s.query(models.ChargingBalanceOrder)
                .order_by(models.ChargingBalanceOrder.created_at.desc())
                .limit(50)
                .all()
            )

            if not orders:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_orders"],
                    show_alert=True,
                )
                return

            # Build keyboard with 3 columns
            order_texts = []
            order_data = []
            for order in orders:
                status_text = TEXTS[lang].get(
                    f"order_status_{order.status.value}", order.status.value
                )
                order_text = (
                    f"#{order.id} - {format_float(order.amount)} - {status_text}"
                )
                order_texts.append(order_text)
                order_data.append(f"admin_view_charge_order_{order.id}")

            order_keyboard = build_keyboard(
                columns=3,
                texts=order_texts,
                buttons_data=order_data,
            )
            order_keyboard.append(
                build_back_button("back_to_orders_settings", lang=lang)
            )
            order_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            text = f"<b>{TEXTS[lang]['charging_balance_orders']}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(order_keyboard),
            )


show_charging_balance_orders_admin_handler = CallbackQueryHandler(
    show_charging_balance_orders_admin,
    "^admin_charging_balance_orders$",
)


async def show_purchase_orders_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            orders = (
                s.query(models.PurchaseOrder)
                .order_by(models.PurchaseOrder.created_at.desc())
                .limit(50)
                .all()
            )

            if not orders:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_orders"],
                    show_alert=True,
                )
                return

            # Build keyboard with 3 columns
            order_texts = []
            order_data = []
            for order in orders:
                item_name = order.item.name if order.item else "N/A"
                status_text = TEXTS[lang].get(
                    f"order_status_{order.status.value}", order.status.value
                )
                order_text = (
                    f"#{order.id} - {escape_html(item_name[:15])} - {status_text}"
                )
                order_texts.append(order_text)
                order_data.append(f"admin_view_purchase_order_{order.id}")

            order_keyboard = build_keyboard(
                columns=3,
                texts=order_texts,
                buttons_data=order_data,
            )
            order_keyboard.append(
                build_back_button("back_to_orders_settings", lang=lang)
            )
            order_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            text = f"<b>{TEXTS[lang]['purchase_orders']}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(order_keyboard),
            )


show_purchase_orders_admin_handler = CallbackQueryHandler(
    show_purchase_orders_admin,
    "^admin_purchase_orders$",
)


async def view_charging_balance_order_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            order_id = int(
                update.callback_query.data.replace("admin_view_charge_order_", "")
            )
        else:
            data = update.callback_query.data.replace("back_to_order_", "")
            _, order_id = data.split("_", 1)
            order_id = int(order_id)

        with models.session_scope() as s:
            order = s.get(models.ChargingBalanceOrder, order_id)
            # Send payment proof if exists
            if order.payment_proof:
                try:
                    await update.callback_query.message.reply_photo(
                        photo=order.payment_proof,
                        caption=TEXTS[lang]["payment_proof"],
                    )
                except:
                    try:
                        await update.callback_query.message.reply_document(
                            document=order.payment_proof,
                            caption=TEXTS[lang]["payment_proof"],
                        )
                    except:
                        pass
            # Use stringify method and add user info
            text = order.stringify(lang)
            text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
            text += f"\n{order.user.stringify(lang)}"

            actions_keyboard = build_order_actions_keyboard(lang, order_id, "charging")
            actions_keyboard.append(
                build_back_button("back_to_admin_charging_balance_orders", lang=lang)
            )
            actions_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(actions_keyboard),
            )


view_charging_balance_order_admin_handler = CallbackQueryHandler(
    view_charging_balance_order_admin,
    r"^admin_view_charge_order_\d+$",
)


async def view_purchase_order_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            order_id = int(
                update.callback_query.data.replace("admin_view_purchase_order_", "")
            )
        else:
            data = update.callback_query.data.replace("back_to_order_", "")
            _, order_id = data.split("_", 1)
            order_id = int(order_id)

        with models.session_scope() as s:
            order = s.get(models.PurchaseOrder, order_id)
            # Use stringify method and add user info
            text = order.stringify(lang)
            text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
            text += f"\n{order.user.stringify(lang)}"

            actions_keyboard = build_order_actions_keyboard(lang, order_id, "purchase")
            actions_keyboard.append(
                build_back_button("back_to_admin_purchase_orders", lang=lang)
            )
            actions_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(actions_keyboard),
            )


view_purchase_order_admin_handler = CallbackQueryHandler(
    view_purchase_order_admin,
    r"^admin_view_purchase_order_\d+$",
)


async def change_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        data = update.callback_query.data.replace("change_status_", "")
        order_type, order_id = data.split("_", 1)
        order_id = int(order_id)

        context.user_data["editing_order_id"] = order_id
        context.user_data["editing_order_type"] = order_type

        if order_type == "charging":
            current_status = None
            with models.session_scope() as s:
                order = s.get(models.ChargingBalanceOrder, order_id)
                if order:
                    current_status = order.status
        else:
            current_status = None
            with models.session_scope() as s:
                order = s.get(models.PurchaseOrder, order_id)
                if order:
                    current_status = order.status

        keyboard = build_order_status_keyboard(lang, current_status, order_type)
        keyboard.append(
            build_back_button(f"back_to_order_{order_type}_{order_id}", lang=lang)
        )
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get("select_order_status", "Select order status:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def set_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        data = update.callback_query.data.replace("set_order_status_", "")
        order_type, status_value = data.split("_", 1)

        order_id = context.user_data.get("editing_order_id")

        with models.session_scope() as s:
            if order_type == "charging":
                order_obj = s.get(models.ChargingBalanceOrder, order_id)
                if order_obj:
                    order_obj.status = models.ChargingOrderStatus(status_value)
                    # If completing, add balance to user
                    if status_value == "completed":
                        user_obj = s.get(models.User, order_obj.user_id)
                        if user_obj:
                            user_obj.balance += order_obj.amount
                    else:
                        user_obj = s.get(models.User, order_obj.user_id)
            else:
                order_obj = s.get(models.PurchaseOrder, order_id)
                if order_obj:
                    order_obj.status = models.PurchaseOrderStatus(status_value)
                    # If refunding, refund balance to user
                    if status_value == "refunded" and order_obj.item:
                        user_obj = s.get(models.User, order_obj.user_id)
                        if user_obj:
                            user_obj.balance += order_obj.item.price
                    else:
                        user_obj = s.get(models.User, order_obj.user_id)

            await update.callback_query.answer(
                text=TEXTS[lang].get("order_status_updated", "Order status updated ✅"),
                show_alert=True,
            )

            # sending notification to user
            try:
                user_lang = user_obj.lang
                status_text = TEXTS[user_lang].get(
                    f"order_status_{status_value}", status_value
                )

                if order_type == "charging":
                    notification_text = TEXTS[user_lang].get(
                        "charging_order_status_changed",
                        "🔔 <b>Charging Balance Order Status Updated</b>\n\n",
                    )
                    notification_text += f"<b>{TEXTS[user_lang].get('order_id', 'Order ID')}:</b> <code>{order_id}</code>\n"
                    notification_text += f"<b>{TEXTS[user_lang].get('order_status', 'Order Status')}:</b> {status_text}\n"
                    notification_text += f"<b>{TEXTS[user_lang].get('order_amount', 'Amount')}:</b> <code>{format_float(order_obj.amount)}</code>"
                else:
                    notification_text = TEXTS[user_lang].get(
                        "purchase_order_status_changed",
                        "🔔 <b>Purchase Order Status Updated</b>\n\n",
                    )
                    notification_text += f"<b>{TEXTS[user_lang].get('order_id', 'Order ID')}:</b> <code>{order_id}</code>\n"
                    notification_text += f"<b>{TEXTS[user_lang].get('order_status', 'Order Status')}:</b> {status_text}"
                    if order_obj.item:
                        notification_text += f"\n<b>{TEXTS[user_lang].get('item_name', 'Item Name')}:</b> {escape_html(order_obj.item.name)}"

                await context.bot.send_message(
                    chat_id=user_obj.user_id,
                    text=notification_text,
                )
            except:
                pass

        # Return to order view by directly calling the view function
        order_type = context.user_data.get("editing_order_type")
        if order_type == "charging":
            # Create a mock callback query data for the view function
            # We'll need to modify the approach - call the view function directly with order_id
            lang = get_lang(update.effective_user.id)
            with models.session_scope() as s:
                order = s.get(models.ChargingBalanceOrder, order_id)
                # Use stringify method and add user info
                text = order.stringify(lang)
                text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
                text += f"\n{order.user.stringify(lang)}"

                actions_keyboard = build_order_actions_keyboard(
                    lang, order_id, "charging"
                )
                actions_keyboard.append(
                    build_back_button(
                        "back_to_admin_charging_balance_orders", lang=lang
                    )
                )
                actions_keyboard.append(
                    build_back_to_home_page_button(lang=lang, is_admin=True)[0]
                )

                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(actions_keyboard),
                )

        else:
            # Purchase order view
            lang = get_lang(update.effective_user.id)
            with models.session_scope() as s:
                order = s.get(models.PurchaseOrder, order_id)
                # Use stringify method and add user info
                text = order.stringify(lang)
                text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
                text += f"\n{order.user.stringify(lang)}"

                actions_keyboard = build_order_actions_keyboard(
                    lang, order_id, "purchase"
                )
                actions_keyboard.append(
                    build_back_button("back_to_admin_purchase_orders", lang=lang)
                )
                actions_keyboard.append(
                    build_back_to_home_page_button(lang=lang, is_admin=True)[0]
                )

                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(actions_keyboard),
                )


back_to_charging_order = view_charging_balance_order_admin
back_to_purchase_order = view_purchase_order_admin


update_order_status_handler = CallbackQueryHandler(
    change_order_status,
    r"^change_status_(charging|purchase)_\d+$",
)

set_order_status_handler = CallbackQueryHandler(
    set_order_status,
    r"^set_order_status_(charging|purchase)_(pending|processing|completed|failed|cancelled|refunded)$",
)

back_to_charging_order_handler = CallbackQueryHandler(
    back_to_charging_order,
    r"^back_to_order_charging_\d+$",
)
back_to_purchase_order_handler = CallbackQueryHandler(
    back_to_purchase_order,
    r"^back_to_order_purchase_\d+$",
)


async def add_order_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        data = update.callback_query.data.replace("add_notes_", "")
        order_type, order_id = data.split("_", 1)
        order_id = int(order_id)

        context.user_data["editing_order_id"] = order_id
        context.user_data["editing_order_type"] = order_type

        back_buttons = [
            build_back_button(f"back_to_order_{order_type}_{order_id}", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=True)[0],
        ]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get("enter_order_notes", "Enter notes for this order:"),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ADD_ORDER_NOTES


async def get_order_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        order_id = context.user_data.get("editing_order_id")
        order_type = context.user_data.get("editing_order_type")
        notes = update.message.text.strip()

        with models.session_scope() as s:
            if order_type == "charging":
                order = s.get(models.ChargingBalanceOrder, order_id)
            else:
                order = s.get(models.PurchaseOrder, order_id)

            if order:
                order.admin_notes = notes

        context.user_data.pop("editing_order_id", None)
        context.user_data.pop("editing_order_type", None)

        await update.message.reply_text(
            text=TEXTS[lang].get("order_notes_added", "Notes added successfully ✅"),
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


add_order_notes_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_order_notes,
            r"^add_notes_(charging|purchase)_\d+$",
        ),
    ],
    states={
        ADD_ORDER_NOTES: [
            MessageHandler(
                callback=get_order_notes,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
    },
    fallbacks=[
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        back_to_purchase_order_handler,
        back_to_charging_order_handler,
    ],
)


back_to_admin_charging_balance_orders = show_charging_balance_orders_admin


back_to_admin_purchase_orders = show_purchase_orders_admin


back_to_admin_charging_balance_orders_handler = CallbackQueryHandler(
    back_to_admin_charging_balance_orders,
    r"^back_to_admin_charging_balance_orders$",
)

back_to_admin_purchase_orders_handler = CallbackQueryHandler(
    back_to_admin_purchase_orders,
    r"^back_to_admin_purchase_orders$",
)
