from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from admin.orders_settings.keyboards import (
    build_orders_settings_keyboard,
    build_order_status_keyboard,
    build_order_actions_keyboard,
    build_orders_list_keyboard,
    ORDERS_PER_PAGE,
)
from common.keyboards import (
    build_back_to_home_page_button,
    build_back_button,
)
from common.lang_dicts import TEXTS, get_lang
from common.common import escape_html, format_float
from custom_filters import PrivateChatAndAdmin, PermissionFilter, OrderNotesReplyFilter, OrderAmountReplyFilter
import models

# Note: Order notes are now handled via reply to order messages


async def orders_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_orders_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
        try:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get("orders_settings_title", "Orders Management"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except:
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=TEXTS[lang].get("orders_settings_title", "Orders Management"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )


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
            keyboard = InlineKeyboardMarkup(actions_keyboard)

            # If payment proof exists, use photo-caption style
            if order.payment_proof:
                # Check if current message has a photo
                current_message = update.callback_query.message
                has_photo = (
                    current_message.photo is not None and len(current_message.photo) > 0
                )

                if has_photo:
                    # Message already has photo, edit caption
                    try:
                        await update.callback_query.edit_message_caption(
                            caption=text,
                            reply_markup=keyboard,
                        )
                    except:
                        # If edit fails, delete and send new photo with caption
                        try:
                            await update.callback_query.message.delete()
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=order.payment_proof,
                                caption=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # If photo fails, try document
                            try:
                                await context.bot.send_document(
                                    chat_id=update.effective_chat.id,
                                    document=order.payment_proof,
                                    caption=text,
                                    reply_markup=keyboard,
                                )
                            except:
                                # Fallback to text message
                                await context.bot.send_message(
                                    chat_id=update.effective_chat.id,
                                    text=text,
                                    reply_markup=keyboard,
                                )
                else:
                    # Message doesn't have photo, need to replace with photo
                    try:
                        await update.callback_query.message.delete()
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=order.payment_proof,
                            caption=text,
                            reply_markup=keyboard,
                        )
                    except:
                        # If photo fails, try document
                        try:
                            await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=order.payment_proof,
                                caption=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # Fallback to text message
                            await update.callback_query.edit_message_text(
                                text=text,
                                reply_markup=keyboard,
                            )
            else:
                # No payment proof, use text message
                # Check if current message has photo (need to replace with text)
                current_message = update.callback_query.message
                has_photo = (
                    current_message.photo is not None and len(current_message.photo) > 0
                )

                if has_photo:
                    # Current message has photo but order doesn't have proof, replace with text
                    try:
                        await update.callback_query.message.delete()
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    except:
                        # If delete fails, try editing caption (will fail but we try)
                        await update.callback_query.edit_message_text(
                            text=text,
                            reply_markup=keyboard,
                        )
                else:
                    # No photo, just edit text
                    await update.callback_query.edit_message_text(
                        text=text,
                        reply_markup=keyboard,
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
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            # Get total count
            total_count = s.query(models.ChargingBalanceOrder).count()

            if total_count == 0:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_orders"],
                    show_alert=True,
                )
                return

            # Calculate pagination
            total_pages = (total_count + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
            page = max(0, min(page, total_pages - 1))
            offset = page * ORDERS_PER_PAGE

            orders = (
                s.query(models.ChargingBalanceOrder)
                .order_by(models.ChargingBalanceOrder.created_at.desc())
                .offset(offset)
                .limit(ORDERS_PER_PAGE)
                .all()
            )

            keyboard = build_orders_list_keyboard(
                orders=orders,
                lang=lang,
                page=page,
                total_pages=total_pages,
                callback_prefix="admin_view_charge_order_",
                back_callback="back_to_orders_settings",
                is_admin=True,
            )

            text = f"<b>{TEXTS[lang]['charging_balance_orders']}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
                
            try:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                )
            except:
                await update.callback_query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard,
                )


async def handle_charging_balance_orders_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination for charging balance orders"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        data = update.callback_query.data
        if data == "page_info":
            await update.callback_query.answer()
            return
        page = int(data.replace("admin_page_charge_order_", ""))
        await show_charging_balance_orders_admin(update, context, page=page)


show_charging_balance_orders_admin_handler = CallbackQueryHandler(
    show_charging_balance_orders_admin,
    "^admin_charging_balance_orders$",
)

charging_balance_orders_pagination_handler = CallbackQueryHandler(
    handle_charging_balance_orders_pagination,
    r"^admin_page_charge_order_\d+$|^page_info$",
)


async def show_purchase_orders_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            # Get total count
            total_count = s.query(models.PurchaseOrder).count()

            if total_count == 0:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_orders"],
                    show_alert=True,
                )
                return

            # Calculate pagination
            total_pages = (total_count + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
            page = max(0, min(page, total_pages - 1))
            offset = page * ORDERS_PER_PAGE

            orders = (
                s.query(models.PurchaseOrder)
                .order_by(models.PurchaseOrder.created_at.desc())
                .offset(offset)
                .limit(ORDERS_PER_PAGE)
                .all()
            )

            keyboard = build_orders_list_keyboard(
                orders=orders,
                lang=lang,
                page=page,
                total_pages=total_pages,
                callback_prefix="admin_view_purchase_order_",
                back_callback="back_to_orders_settings",
                is_admin=True,
            )

            text = f"<b>{TEXTS[lang]['purchase_orders']}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
            )


async def handle_purchase_orders_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination for purchase orders"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        data = update.callback_query.data
        if data == "page_info":
            await update.callback_query.answer()
            return
        page = int(data.replace("admin_page_purchase_order_", ""))
        await show_purchase_orders_admin(update, context, page=page)


show_purchase_orders_admin_handler = CallbackQueryHandler(
    show_purchase_orders_admin,
    "^admin_purchase_orders$",
)

purchase_orders_pagination_handler = CallbackQueryHandler(
    handle_purchase_orders_pagination,
    r"^admin_page_purchase_order_\d+$|^page_info$",
)


async def show_api_purchase_orders_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0
):
    """Show API purchase orders for admin (read-only, no actions)"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            # Get total count
            total_count = s.query(models.ApiPurchaseOrder).count()

            if total_count == 0:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_orders"],
                    show_alert=True,
                )
                return

            # Calculate pagination
            total_pages = (total_count + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
            page = max(0, min(page, total_pages - 1))
            offset = page * ORDERS_PER_PAGE

            orders = (
                s.query(models.ApiPurchaseOrder)
                .order_by(models.ApiPurchaseOrder.created_at.desc())
                .offset(offset)
                .limit(ORDERS_PER_PAGE)
                .all()
            )

            keyboard = build_orders_list_keyboard(
                orders=orders,
                lang=lang,
                page=page,
                total_pages=total_pages,
                callback_prefix="admin_view_api_purchase_order_",
                back_callback="back_to_orders_settings",
                is_admin=True,
            )

            text = f"<b>{TEXTS[lang].get('api_purchase_orders', 'Instant Purchase Orders ⚡')}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
            )


async def view_api_purchase_order_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """View API purchase order details (read-only)"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        order_id = int(
            update.callback_query.data.replace("admin_view_api_purchase_order_", "")
        )

        with models.session_scope() as s:
            order = s.get(models.ApiPurchaseOrder, order_id)
            if not order:
                await update.callback_query.answer(
                    text=TEXTS[lang]["order_not_found"],
                    show_alert=True,
                )
                return

            # Use stringify method to build order details text
            text = order.stringify(lang)

            back_buttons = [
                build_back_button("back_to_api_purchase_orders_admin", lang=lang),
                build_back_to_home_page_button(lang=lang, is_admin=True)[0],
            ]

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )


async def handle_api_purchase_orders_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination for API purchase orders"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        data = update.callback_query.data
        if data == "page_info":
            await update.callback_query.answer()
            return
        page = int(data.replace("admin_page_api_purchase_order_", ""))
        await show_api_purchase_orders_admin(update, context, page=page)


back_to_api_purchase_orders_admin = show_api_purchase_orders_admin

show_api_purchase_orders_admin_handler = CallbackQueryHandler(
    show_api_purchase_orders_admin,
    "^admin_api_purchase_orders$",
)

view_api_purchase_order_admin_handler = CallbackQueryHandler(
    view_api_purchase_order_admin,
    r"^admin_view_api_purchase_order_\d+$",
)

api_purchase_orders_pagination_handler = CallbackQueryHandler(
    handle_api_purchase_orders_pagination,
    r"^admin_page_api_purchase_order_\d+$|^page_info$",
)

back_to_api_purchase_orders_admin_handler = CallbackQueryHandler(
    back_to_api_purchase_orders_admin,
    r"^back_to_api_purchase_orders_admin$",
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
            keyboard = InlineKeyboardMarkup(actions_keyboard)

            # If payment proof exists, use photo-caption style
            if order.payment_proof:
                # Check if current message has a photo
                current_message = update.callback_query.message
                has_photo = (
                    current_message.photo is not None and len(current_message.photo) > 0
                )

                if has_photo:
                    # Message already has photo, edit caption
                    try:
                        await update.callback_query.edit_message_caption(
                            caption=text,
                            reply_markup=keyboard,
                        )
                    except:
                        # If edit fails, delete and send new photo with caption
                        try:
                            await update.callback_query.message.delete()
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=order.payment_proof,
                                caption=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # If photo fails, try document
                            try:
                                await context.bot.send_document(
                                    chat_id=update.effective_chat.id,
                                    document=order.payment_proof,
                                    caption=text,
                                    reply_markup=keyboard,
                                )
                            except:
                                # Fallback to text message
                                await context.bot.send_message(
                                    chat_id=update.effective_chat.id,
                                    text=text,
                                    reply_markup=keyboard,
                                )
                else:
                    # Message doesn't have photo, need to replace with photo
                    try:
                        await update.callback_query.message.delete()
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=order.payment_proof,
                            caption=text,
                            reply_markup=keyboard,
                        )
                    except:
                        # If photo fails, try document
                        try:
                            await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=order.payment_proof,
                                caption=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # Fallback to text message
                            await update.callback_query.edit_message_text(
                                text=text,
                                reply_markup=keyboard,
                            )
            else:
                # No payment proof, use text message
                # Check if current message has photo (need to replace with text)
                current_message = update.callback_query.message
                has_photo = (
                    current_message.photo is not None and len(current_message.photo) > 0
                )

                if has_photo:
                    # Current message has photo but order doesn't have proof, replace with text
                    try:
                        await update.callback_query.message.delete()
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    except:
                        # If delete fails, try editing caption (will fail but we try)
                        await update.callback_query.edit_message_text(
                            text=text,
                            reply_markup=keyboard,
                        )
                else:
                    # No photo, just edit text
                    await update.callback_query.edit_message_text(
                        text=text,
                        reply_markup=keyboard,
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

        if update.callback_query.message.photo:
            await update.callback_query.edit_message_caption(
                caption=TEXTS[lang].get("select_order_status", "Select order status:"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
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
            user_obj = None
            if order_type == "charging":
                order_obj = s.get(models.ChargingBalanceOrder, order_id)
                if order_obj:
                    # Get user first
                    user_obj = s.get(models.User, order_obj.user_id)
                    if not user_obj:
                        await update.callback_query.answer(
                            text=TEXTS[lang].get("user_not_found", "User not found ❌"),
                            show_alert=True,
                        )
                        return
                    
                    # Save old status before changing
                    old_status = order_obj.status
                    new_status = models.ChargingOrderStatus(status_value)
                    
                    # Only process balance changes if status actually changed
                    if old_status != new_status:
                        # If changing TO completed: add balance
                        if old_status != models.ChargingOrderStatus.COMPLETED and new_status == models.ChargingOrderStatus.COMPLETED:
                            user_obj.balance += order_obj.amount
                        # If changing FROM completed to any other status: deduct balance
                        elif old_status == models.ChargingOrderStatus.COMPLETED and new_status != models.ChargingOrderStatus.COMPLETED:
                            user_obj.balance -= order_obj.amount
                    
                    # Update status
                    order_obj.status = new_status
            else:
                order_obj = s.get(models.PurchaseOrder, order_id)
                if order_obj:
                    # Get user first
                    user_obj = s.get(models.User, order_obj.user_id)
                    if not user_obj:
                        await update.callback_query.answer(
                            text=TEXTS[lang].get("user_not_found", "User not found ❌"),
                            show_alert=True,
                        )
                        return
                    
                    # Save old status before changing
                    old_status = order_obj.status
                    new_status = models.PurchaseOrderStatus(status_value)
                    
                    # Only process balance changes if status actually changed and item exists
                    # Note: Balance is deducted when order is created (PENDING status)
                    # So we need to refund when changing to REFUNDED, CANCELLED, or FAILED
                    # And deduct again when changing from these states back to active states
                    if old_status != new_status and order_obj.item:
                        # States that require refund (balance was already deducted at creation)
                        refund_states = [
                            models.PurchaseOrderStatus.REFUNDED,
                            models.PurchaseOrderStatus.CANCELLED,
                            models.PurchaseOrderStatus.FAILED,
                        ]
                        
                        # States that are active (balance was deducted at creation)
                        active_states = [
                            models.PurchaseOrderStatus.PENDING,
                            models.PurchaseOrderStatus.PROCESSING,
                            models.PurchaseOrderStatus.COMPLETED,
                        ]
                        
                        # If changing FROM active state TO refund state: refund balance
                        if old_status in active_states and new_status in refund_states:
                            user_obj.balance += order_obj.item.price
                        # If changing FROM refund state TO active state: deduct balance again
                        elif old_status in refund_states and new_status in active_states:
                            user_obj.balance -= order_obj.item.price
                    
                    # Update status
                    order_obj.status = new_status
            
            if not order_obj:
                await update.callback_query.answer(
                    text=TEXTS[lang].get("order_not_found", "Order not found ❌"),
                    show_alert=True,
                )
                return
            
            if not user_obj:
                await update.callback_query.answer(
                    text=TEXTS[lang].get("user_not_found", "User not found ❌"),
                    show_alert=True,
                )
                return

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
            # Return to order view with photo-caption handling
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
                keyboard = InlineKeyboardMarkup(actions_keyboard)

                # If payment proof exists, use photo-caption style
                if order.payment_proof:
                    # Check if current message has a photo
                    current_message = update.callback_query.message
                    has_photo = (
                        current_message.photo is not None
                        and len(current_message.photo) > 0
                    )

                    if has_photo:
                        # Message already has photo, edit caption
                        try:
                            await update.callback_query.edit_message_caption(
                                caption=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # If edit fails, delete and send new photo with caption
                            try:
                                await update.callback_query.message.delete()
                                await context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=order.payment_proof,
                                    caption=text,
                                    reply_markup=keyboard,
                                )
                            except:
                                # If photo fails, try document
                                try:
                                    await context.bot.send_document(
                                        chat_id=update.effective_chat.id,
                                        document=order.payment_proof,
                                        caption=text,
                                        reply_markup=keyboard,
                                    )
                                except:
                                    # Fallback to text message
                                    await context.bot.send_message(
                                        chat_id=update.effective_chat.id,
                                        text=text,
                                        reply_markup=keyboard,
                                    )
                    else:
                        # Message doesn't have photo, need to replace with photo
                        try:
                            await update.callback_query.message.delete()
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=order.payment_proof,
                                caption=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # If photo fails, try document
                            try:
                                await context.bot.send_document(
                                    chat_id=update.effective_chat.id,
                                    document=order.payment_proof,
                                    caption=text,
                                    reply_markup=keyboard,
                                )
                            except:
                                # Fallback to text message
                                await update.callback_query.edit_message_text(
                                    text=text,
                                    reply_markup=keyboard,
                                )
                else:
                    # No payment proof, use text message
                    # Check if current message has photo (need to replace with text)
                    current_message = update.callback_query.message
                    has_photo = (
                        current_message.photo is not None
                        and len(current_message.photo) > 0
                    )

                    if has_photo:
                        # Current message has photo but order doesn't have proof, replace with text
                        try:
                            await update.callback_query.message.delete()
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=text,
                                reply_markup=keyboard,
                            )
                        except:
                            # If delete fails, try editing caption (will fail but we try)
                            await update.callback_query.edit_message_text(
                                text=text,
                                reply_markup=keyboard,
                            )
                    else:
                        # No photo, just edit text
                        await update.callback_query.edit_message_text(
                            text=text,
                            reply_markup=keyboard,
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
    """Handler for Add Notes button - prompts admin to reply to order message"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        data = update.callback_query.data.replace("add_notes_", "")
        order_type, order_id = data.split("_", 1)
        order_id = int(order_id)

        # Send instruction message asking admin to reply to the order message
        instruction_text = TEXTS[lang].get(
            "reply_to_order_for_notes",
            "📝 Reply to the order message above to add notes to this order.",
        )

        await update.callback_query.answer(
            text=instruction_text,
            show_alert=True,
        )


async def edit_order_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for Edit Amount button - prompts admin to reply to order message with new amount"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ORDERS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        data = update.callback_query.data.replace("edit_amount_", "")
        order_type, order_id = data.split("_", 1)
        order_id = int(order_id)

        # Only allow editing amount for charging orders
        if order_type != "charging":
            await update.callback_query.answer(
                text=TEXTS[lang].get("invalid_action", "Invalid action ❌"),
                show_alert=True,
            )
            return

        # Send instruction message asking admin to reply to the order message
        instruction_text = TEXTS[lang].get(
            "reply_to_order_for_amount",
            "💰 Reply to the order message above with the new amount (number only).",
        )

        await update.callback_query.answer(
            text=instruction_text,
            show_alert=True,
        )


async def get_order_notes_from_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handler for processing order notes from reply to order message"""
    if not PermissionFilter(models.Permission.MANAGE_ORDERS).filter(update):
        return
    lang = get_lang(update.effective_user.id)
    notes = update.message.text.strip()

    if not notes:
        await update.message.reply_text(
            text=TEXTS[lang].get("notes_empty", "Notes cannot be empty ❌"),
        )
        return

    # Extract order info from the replied message
    replied_message = update.message.reply_to_message
    order_id = None
    order_type = None

    # Try to extract from keyboard callback data
    if replied_message.reply_markup and hasattr(
        replied_message.reply_markup, "inline_keyboard"
    ):
        keyboard = replied_message.reply_markup
        for row in keyboard.inline_keyboard:
            for button in row:
                callback_data = button.callback_data
                if callback_data:
                    # Check for order view callbacks
                    if callback_data.startswith("admin_view_charge_order_"):
                        order_id = int(
                            callback_data.replace("admin_view_charge_order_", "")
                        )
                        order_type = "charging"
                        break
                    elif callback_data.startswith("admin_view_purchase_order_"):
                        order_id = int(
                            callback_data.replace("admin_view_purchase_order_", "")
                        )
                        order_type = "purchase"
                        break
                    # Check for action callbacks that contain order info
                    elif callback_data.startswith("change_status_charging_"):
                        order_id = int(
                            callback_data.replace("change_status_charging_", "")
                        )
                        order_type = "charging"
                        break
                    elif callback_data.startswith("change_status_purchase_"):
                        order_id = int(
                            callback_data.replace("change_status_purchase_", "")
                        )
                        order_type = "purchase"
                        break
                    elif callback_data.startswith("add_notes_charging_"):
                        order_id = int(callback_data.replace("add_notes_charging_", ""))
                        order_type = "charging"
                        break
                    elif callback_data.startswith("add_notes_purchase_"):
                        order_id = int(callback_data.replace("add_notes_purchase_", ""))
                        order_type = "purchase"
                        break
            if order_id:
                break

    # If not found in keyboard, try to extract from message text/caption
    if not order_id:
        text = replied_message.text or replied_message.caption or ""
        # Look for "Order ID: <code>123</code>" pattern
        import re

        order_id_match = re.search(
            r"Order ID[:\s]*<code>(\d+)</code>", text, re.IGNORECASE
        )
        if not order_id_match:
            order_id_match = re.search(r"رقم الطلب[:\s]*<code>(\d+)</code>", text)

        if order_id_match:
            order_id = int(order_id_match.group(1))
            # Try to determine order type from text
            if (
                "charging" in text.lower()
                or "شحن" in text
                or "charging" in text.lower()
            ):
                order_type = "charging"
            elif "purchase" in text.lower() or "شراء" in text:
                order_type = "purchase"
            else:
                # Default: try charging first, then purchase
                with models.session_scope() as s:
                    order = s.get(models.ChargingBalanceOrder, order_id)
                    if order:
                        order_type = "charging"
                    else:
                        order = s.get(models.PurchaseOrder, order_id)
                        if order:
                            order_type = "purchase"

    if not order_id or not order_type:
        await update.message.reply_text(
            text=TEXTS[lang].get(
                "order_not_found_in_reply",
                "Could not identify the order from the replied message. Please use the 'Add Notes' button on the order message.",
            ),
        )
        return

    # Save notes to order
    with models.session_scope() as s:
        from sqlalchemy.orm import joinedload
        
        if order_type == "charging":
            order = (
                s.query(models.ChargingBalanceOrder)
                .options(
                    joinedload(models.ChargingBalanceOrder.payment_method_address).joinedload(models.PaymentMethodAddress.payment_method),
                    joinedload(models.ChargingBalanceOrder.user)
                )
                .filter(models.ChargingBalanceOrder.id == order_id)
                .first()
            )
        else:
            order = (
                s.query(models.PurchaseOrder)
                .options(
                    joinedload(models.PurchaseOrder.item).joinedload(models.Item.game),
                    joinedload(models.PurchaseOrder.user)
                )
                .filter(models.PurchaseOrder.id == order_id)
                .first()
            )

        if not order:
            await update.message.reply_text(
                text=TEXTS[lang].get("order_not_found", "Order not found ❌"),
            )
            return

        order.admin_notes = notes

    # Build updated order message
    text = order.stringify(lang)
    text += f"\n\n<b>{TEXTS[lang].get('user', 'User')}:</b>"
    text += f"\n{order.user.stringify(lang)}"

    actions_keyboard = build_order_actions_keyboard(lang, order_id, order_type)
    if order_type == "charging":
        actions_keyboard.append(
            build_back_button("back_to_admin_charging_balance_orders", lang=lang)
        )
    else:
        actions_keyboard.append(
            build_back_button("back_to_admin_purchase_orders", lang=lang)
        )
    actions_keyboard.append(
        build_back_to_home_page_button(lang=lang, is_admin=True)[0]
    )
    keyboard = InlineKeyboardMarkup(actions_keyboard)

    # Send success message
    await update.message.reply_text(
        text=TEXTS[lang].get("order_notes_added", "Notes added successfully ✅"),
    )

    # Resend the updated order message
    chat_id = update.effective_chat.id
    
    # Check if original message had a photo (for charging orders with payment proof)
    if order_type == "charging" and hasattr(order, 'payment_proof') and order.payment_proof:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=order.payment_proof,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except:
            # If photo fails, try document
            try:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=order.payment_proof,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            except:
                # Fallback to text message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    else:
        # No payment proof, send as text message
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# Separate handlers instead of ConversationHandler
add_order_notes_handler = CallbackQueryHandler(
    add_order_notes,
    r"^add_notes_(charging|purchase)_\d+$",
)

async def get_order_amount_from_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handler for processing order amount edit from reply to order message"""
    if not PermissionFilter(models.Permission.MANAGE_ORDERS).filter(update):
        return
    lang = get_lang(update.effective_user.id)
    amount_text = update.message.text.strip()

    # Validate that the input is a valid number
    try:
        new_amount = float(amount_text)
        if new_amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        await update.message.reply_text(
            text=TEXTS[lang].get(
                "invalid_amount",
                "Invalid amount ❌\nPlease send a valid positive number.",
            ),
        )
        return

    # Extract order info from the replied message
    replied_message = update.message.reply_to_message
    order_id = None

    # Try to extract from keyboard callback data
    if replied_message.reply_markup and hasattr(
        replied_message.reply_markup, "inline_keyboard"
    ):
        keyboard = replied_message.reply_markup
        for row in keyboard.inline_keyboard:
            for button in row:
                callback_data = button.callback_data
                if callback_data and callback_data.startswith("edit_amount_charging_"):
                    order_id = int(callback_data.replace("edit_amount_charging_", ""))
                    break
            if order_id:
                break

    # If not found in keyboard, try to extract from message text/caption
    if not order_id:
        text = replied_message.text or replied_message.caption or ""
        import re

        order_id_match = re.search(
            r"Order ID[:\s]*<code>(\d+)</code>", text, re.IGNORECASE
        )
        if not order_id_match:
            order_id_match = re.search(r"رقم الطلب[:\s]*<code>(\d+)</code>", text)

        if order_id_match:
            order_id = int(order_id_match.group(1))
            # Verify it's a charging order
            with models.session_scope() as s:
                order = s.get(models.ChargingBalanceOrder, order_id)
                if not order:
                    order_id = None

    if not order_id:
        await update.message.reply_text(
            text=TEXTS[lang].get(
                "order_not_found_in_reply",
                "Could not identify the order from the replied message. Please use the 'Edit Amount' button on the order message.",
            ),
        )
        return

    # Save new amount to order and update balance accordingly
    with models.session_scope() as s:
        from sqlalchemy.orm import joinedload

        order = (
            s.query(models.ChargingBalanceOrder)
            .options(
                joinedload(models.ChargingBalanceOrder.payment_method_address).joinedload(
                    models.PaymentMethodAddress.payment_method
                ),
                joinedload(models.ChargingBalanceOrder.user),
            )
            .filter(models.ChargingBalanceOrder.id == order_id)
            .first()
        )

        if not order:
            await update.message.reply_text(
                text=TEXTS[lang].get("order_not_found", "Order not found ❌"),
            )
            return

        # Get user
        user = s.get(models.User, order.user_id)
        if not user:
            await update.message.reply_text(
                text=TEXTS[lang].get("user_not_found", "User not found ❌"),
            )
            return

        # Save old amount (convert to float for calculation)
        old_amount = float(order.amount)
        
        # Calculate difference
        amount_difference = new_amount - old_amount
        
        # Update balance only if order status is COMPLETED
        # (because balance is only added to user when status becomes completed)
        if order.status == models.ChargingOrderStatus.COMPLETED:
            # Adjust balance based on the difference
            # Convert amount_difference to Decimal to match user.balance type
            from decimal import Decimal
            user.balance += Decimal(str(amount_difference))
        
        # Update amount
        order.amount = new_amount

    # Build updated order message
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
    keyboard = InlineKeyboardMarkup(actions_keyboard)

    # Send success message
    from common.common import format_float

    await update.message.reply_text(
        text=TEXTS[lang].get(
            "order_amount_updated",
            "Amount updated successfully ✅\nOld amount: {old_amount} SDG\nNew amount: {new_amount} SDG",
        ).format(
            old_amount=format_float(old_amount),
            new_amount=format_float(new_amount),
        ),
    )

    # Resend the updated order message
    chat_id = update.effective_chat.id

    # Check if original message had a photo (for charging orders with payment proof)
    if hasattr(order, "payment_proof") and order.payment_proof:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=order.payment_proof,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except:
            # If photo fails, try document
            try:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=order.payment_proof,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            except:
                # Fallback to text message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    else:
        # No payment proof, send as text message
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# Separate handlers instead of ConversationHandler
add_order_notes_handler = CallbackQueryHandler(
    add_order_notes,
    r"^add_notes_(charging|purchase)_\d+$",
)

edit_order_amount_handler = CallbackQueryHandler(
    edit_order_amount,
    r"^edit_amount_charging_\d+$",
)

get_order_notes_handler = MessageHandler(
    filters=(filters.REPLY & PrivateChatAndAdmin() & OrderNotesReplyFilter()),
    callback=get_order_notes_from_reply,
)

get_order_amount_handler = MessageHandler(
    filters=(filters.REPLY & filters.Regex(r"^\d+(\.\d+)?$") & PrivateChatAndAdmin() & OrderAmountReplyFilter()),
    callback=get_order_amount_from_reply,
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
