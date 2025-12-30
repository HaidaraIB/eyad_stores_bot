from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from user.user_settings.keyboards import (
    build_settings_keyboard,
    build_profile_keyboard,
    build_order_type_keyboard,
)
from common.keyboards import (
    build_back_to_home_page_button,
    build_keyboard,
    build_back_button,
    build_user_keyboard,
)
from common.lang_dicts import TEXTS, get_lang
from common.back_to_home_page import back_to_user_home_page_handler
from common.common import escape_html, format_float
from custom_filters import PrivateChat
from Config import Config
from start import start_command, admin_command
import models


async def user_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["settings"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


user_settings_handler = CallbackQueryHandler(
    user_settings,
    "^user_settings$|^back_to_user_settings$",
)


async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        if update.callback_query.data in models.Language._member_names_:
            lang = models.Language[update.callback_query.data]
            with models.session_scope() as s:
                user = s.get(models.User, update.effective_user.id)
                user.lang = lang
            await update.callback_query.answer(
                text=TEXTS[lang]["change_lang_success"],
                show_alert=True,
            )

        else:
            lang = get_lang(update.effective_user.id)

        keyboard = build_keyboard(
            columns=2,
            texts=[l.value for l in models.Language],
            buttons_data=[l.name for l in models.Language],
        )
        keyboard.append(build_back_button(data="back_to_user_settings", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["change_lang"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


change_lang_handler = CallbackQueryHandler(
    change_lang,
    lambda x: x in [l.name for l in models.Language] + ["change_lang"],
)


# Profile handler
async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            user = s.get(models.User, update.effective_user.id)
            balance = format_float(user.balance)

        keyboard = build_profile_keyboard(lang)
        keyboard.append(build_back_button("back_to_user_settings", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])

        text = TEXTS[lang]["profile_title"]
        text += f"\n\n{TEXTS[lang]['current_balance'].format(balance=balance)}"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


user_profile_handler = CallbackQueryHandler(
    user_profile,
    "^user_profile$|^back_to_user_profile$",
)


# Charging balance order conversation states
(
    CHARGE_BALANCE_AMOUNT,
    CHARGE_BALANCE_PAYMENT_METHOD,
    CHARGE_BALANCE_PAYMENT_ADDRESS,
    CHARGE_BALANCE_PROOF,
) = range(4)


async def charge_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button("back_to_user_profile", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["enter_charge_amount"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return CHARGE_BALANCE_AMOUNT


async def get_charge_balance_payment_method(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            pm_id = int(update.callback_query.data.replace("charge_pm_", ""))
            context.user_data["charge_balance_pm_id"] = pm_id

        with models.session_scope() as s:
            pm_id = context.user_data.get("charge_balance_pm_id")
            payment_method = s.get(models.PaymentMethod, pm_id)
            addresses = (
                s.query(models.PaymentMethodAddress)
                .filter(
                    models.PaymentMethodAddress.payment_method_id == pm_id,
                    models.PaymentMethodAddress.is_active == True,
                )
                .order_by(models.PaymentMethodAddress.priority)
                .all()
            )

            if not addresses:
                pm_name = payment_method.name if payment_method else "N/A"
                await update.callback_query.answer(
                    text=TEXTS[lang]["payment_method_paused"].format(pm_name=pm_name),
                    show_alert=True,
                )
                return CHARGE_BALANCE_PAYMENT_METHOD

            address_keyboard = build_keyboard(
                columns=1,
                texts=[
                    (
                        addr.label
                        if addr.label
                        else f"{TEXTS[lang].get('address', 'Address')} #{addr.id}"
                    )
                    for addr in addresses
                ],
                buttons_data=[f"charge_addr_{addr.id}" for addr in addresses],
            )
            address_keyboard.append(
                build_back_button("back_to_charge_balance_pm", lang=lang)
            )
            address_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_payment_address"],
                reply_markup=InlineKeyboardMarkup(address_keyboard),
            )
        return CHARGE_BALANCE_PAYMENT_ADDRESS


back_to_charge_balance_pm = charge_balance


async def get_charge_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        if update.message:
            amount = float(update.message.text.strip())
            context.user_data["charge_balance_amount"] = amount

        with models.session_scope() as s:
            payment_methods = (
                s.query(models.PaymentMethod)
                .filter(models.PaymentMethod.is_active == True)
                .all()
            )

            if not payment_methods:
                await update.message.reply_text(
                    text=TEXTS[lang]["no_payment_methods"],
                )
                return ConversationHandler.END

            pm_keyboard = build_keyboard(
                columns=1,
                texts=[pm.name for pm in payment_methods],
                buttons_data=[f"charge_pm_{pm.id}" for pm in payment_methods],
            )
            pm_keyboard.append(
                build_back_button("back_to_charge_balance_amount", lang=lang)
            )
            pm_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )
            if update.message:
                await update.message.reply_text(
                    text=TEXTS[lang]["select_payment_method"],
                    reply_markup=InlineKeyboardMarkup(pm_keyboard),
                )
            else:
                await update.callback_query.edit_message_text(
                    text=TEXTS[lang]["select_payment_method"],
                    reply_markup=InlineKeyboardMarkup(pm_keyboard),
                )

        return CHARGE_BALANCE_PAYMENT_METHOD


back_to_charge_balance_amount = get_charge_balance_payment_method


async def get_charge_balance_payment_address(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            addr_id = int(update.callback_query.data.replace("charge_addr_", ""))
            context.user_data["charge_balance_addr_id"] = addr_id

        with models.session_scope() as s:
            pm_id = context.user_data.get("charge_balance_pm_id")
            addr_id = context.user_data.get("charge_balance_addr_id")
            payment_method = s.get(models.PaymentMethod, pm_id)
            address = s.get(models.PaymentMethodAddress, addr_id)

            # Build message with selected address and instructions
            pm_type = payment_method.type.value
            instruction_key = f"charge_balance_instructions_{pm_type}"
            instruction_text = TEXTS[lang].get(
                instruction_key, TEXTS[lang]["charge_balance_instructions"]
            )

            text = f"<b>{escape_html(payment_method.name)}</b>\n\n"
            text += f"{instruction_text}\n\n"

            # Display selected address
            text += f"<b>"
            if address.label:
                text += f"{escape_html(address.label)}"
            else:
                text += f"{TEXTS[lang].get('address', 'Address')} #{address.id}"
            text += f"</b>\n"
            text += f"<code>{escape_html(address.address)}</code>\n"

            if address.account_name:
                text += f"{TEXTS[lang].get('account_name', 'Account Name')}: {escape_html(address.account_name)}\n"
            if address.additional_info:
                text += f"{escape_html(address.additional_info)}\n"

            back_buttons = [
                build_back_button("back_to_charge_balance_addr", lang=lang),
                build_back_to_home_page_button(lang=lang, is_admin=False)[0],
            ]

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return CHARGE_BALANCE_PROOF


back_to_charge_balance_addr = get_charge_balance_amount


async def get_charge_balance_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        addr_id = context.user_data.get("charge_balance_addr_id")
        amount = context.user_data.get("charge_balance_amount")

        # Get file ID from photo or document
        payment_proof = None
        if update.message.photo:
            payment_proof = update.message.photo[-1].file_id
        elif update.message.document:
            payment_proof = update.message.document.file_id
        else:
            # Payment proof is mandatory
            await update.message.reply_text(
                text=TEXTS[lang]["upload_payment_proof"],
            )
            return CHARGE_BALANCE_PROOF

        with models.session_scope() as s:
            new_order = models.ChargingBalanceOrder(
                user_id=update.effective_user.id,
                payment_method_address_id=addr_id,
                amount=amount,
                status=models.ChargingOrderStatus.PENDING,
                payment_proof=payment_proof,
            )
            s.add(new_order)
            s.flush()
            order_id = new_order.id

        # Clean up user_data
        context.user_data.pop("charge_balance_pm_id", None)
        context.user_data.pop("charge_balance_addr_id", None)
        context.user_data.pop("charge_balance_amount", None)

        await update.message.reply_text(
            text=TEXTS[lang]["charge_order_submitted"].format(order_id=order_id),
        )

        # Notify all admins with MANAGE_ORDERS permission
        try:
            notification_text = f"🔔 <b>New Charging Balance Order</b>\n\n"
            notification_text += f"Order ID: <code>{order_id}</code>\n"
            notification_text += f"User: {update.effective_user.mention_html()}\n"
            notification_text += f"Amount: <code>{format_float(amount)}</code>\n"
            notification_text += (
                f"Status: {TEXTS[models.Language.ENGLISH]['order_status_pending']}"
            )

            # Get all admins with MANAGE_ORDERS permission (including owner)
            with models.session_scope() as s:
                # Get owner
                admin_ids = [Config.OWNER_ID]

                # Get all admins with MANAGE_ORDERS permission
                permissions = (
                    s.query(models.AdminPermission)
                    .filter(
                        models.AdminPermission.permission
                        == models.Permission.MANAGE_ORDERS
                    )
                    .all()
                )

                for perm in permissions:
                    if perm.admin_id not in admin_ids:
                        admin_ids.append(perm.admin_id)

            # Send notification to all admins
            for admin_id in admin_ids:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=notification_text,
                    )
                    # Send payment proof
                    if payment_proof:
                        try:
                            await context.bot.send_photo(
                                chat_id=admin_id,
                                photo=payment_proof,
                                caption=f"Payment Proof - Order #{order_id}",
                            )
                        except:
                            try:
                                await context.bot.send_document(
                                    chat_id=admin_id,
                                    document=payment_proof,
                                    caption=f"Payment Proof - Order #{order_id}",
                                )
                            except:
                                pass
                except:
                    continue
        except:
            pass
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_user_keyboard(lang),
        )
        return ConversationHandler.END


charge_balance_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            charge_balance,
            r"^charge_balance$",
        ),
    ],
    states={
        CHARGE_BALANCE_AMOUNT: [
            MessageHandler(
                callback=get_charge_balance_amount,
                filters=filters.Regex("^[0-9]+\.?[0-9]*$"),
            ),
        ],
        CHARGE_BALANCE_PAYMENT_METHOD: [
            CallbackQueryHandler(
                get_charge_balance_payment_method,
                r"^charge_pm_\d+$",
            ),
        ],
        CHARGE_BALANCE_PAYMENT_ADDRESS: [
            CallbackQueryHandler(
                get_charge_balance_payment_address,
                r"^charge_addr_\d+$",
            ),
        ],
        CHARGE_BALANCE_PROOF: [
            MessageHandler(
                callback=get_charge_balance_proof,
                filters=filters.PHOTO | filters.Document.ALL,
            ),
        ],
    },
    fallbacks=[
        start_command,
        admin_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_charge_balance_pm, r"^back_to_charge_balance_pm$"),
        CallbackQueryHandler(
            back_to_charge_balance_addr, r"^back_to_charge_balance_addr$"
        ),
        CallbackQueryHandler(
            back_to_charge_balance_amount, r"^back_to_charge_balance_amount$"
        ),
    ],
)


# My Orders handlers
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_order_type_keyboard(lang)
        keyboard.append(build_back_button("back_to_user_profile", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=False)[0])

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["select_order_type"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


my_orders_handler = CallbackQueryHandler(
    my_orders,
    "^my_orders$|^back_to_my_orders$",
)


async def show_charging_balance_orders(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            orders = (
                s.query(models.ChargingBalanceOrder)
                .filter(models.ChargingBalanceOrder.user_id == update.effective_user.id)
                .order_by(models.ChargingBalanceOrder.created_at.desc())
                .limit(10)
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
                order_text = f"#{order.id} - {format_float(order.amount)}"
                order_texts.append(order_text)
                order_data.append(f"view_charge_order_{order.id}")

            order_keyboard = build_keyboard(
                columns=3,
                texts=order_texts,
                buttons_data=order_data,
            )
            order_keyboard.append(build_back_button("back_to_my_orders", lang=lang))
            order_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )

            text = f"<b>{TEXTS[lang]['charging_balance_orders']}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(order_keyboard),
            )


async def show_purchase_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            orders = (
                s.query(models.PurchaseOrder)
                .filter(models.PurchaseOrder.user_id == update.effective_user.id)
                .order_by(models.PurchaseOrder.created_at.desc())
                .limit(10)
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
                order_text = f"#{order.id} - {escape_html(item_name[:15])}"
                order_texts.append(order_text)
                order_data.append(f"view_purchase_order_{order.id}")

            order_keyboard = build_keyboard(
                columns=3,
                texts=order_texts,
                buttons_data=order_data,
            )
            order_keyboard.append(build_back_button("back_to_my_orders", lang=lang))
            order_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )

            text = f"<b>{TEXTS[lang]['purchase_orders']}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(order_keyboard),
            )


async def view_charging_balance_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        order_id = int(update.callback_query.data.replace("view_charge_order_", ""))

        with models.session_scope() as s:
            order = s.get(models.ChargingBalanceOrder, order_id)
            if not order or order.user_id != update.effective_user.id:
                await update.callback_query.answer(
                    text=TEXTS[lang]["order_not_found"],
                    show_alert=True,
                )
                return

            # Use stringify method to build order details text
            text = order.stringify(lang)

            back_buttons = [
                build_back_button("back_to_charging_balance_orders", lang=lang),
                build_back_to_home_page_button(lang=lang, is_admin=False)[0],
            ]

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )


async def view_purchase_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        order_id = int(update.callback_query.data.replace("view_purchase_order_", ""))

        with models.session_scope() as s:
            order = s.get(models.PurchaseOrder, order_id)
            if not order or order.user_id != update.effective_user.id:
                await update.callback_query.answer(
                    text=TEXTS[lang]["order_not_found"],
                    show_alert=True,
                )
                return

            # Use stringify method to build order details text
            text = order.stringify(lang)

            back_buttons = [
                build_back_button("back_to_purchase_orders", lang=lang),
                build_back_to_home_page_button(lang=lang, is_admin=False)[0],
            ]

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )


back_to_charging_balance_orders = show_charging_balance_orders
back_to_purchase_orders = show_purchase_orders


back_to_charging_balance_orders_handler = CallbackQueryHandler(
    back_to_charging_balance_orders,
    r"^back_to_charging_balance_orders$",
)
back_to_purchase_orders_handler = CallbackQueryHandler(
    back_to_purchase_orders,
    r"^back_to_purchase_orders$",
)

show_charging_balance_orders_handler = CallbackQueryHandler(
    show_charging_balance_orders,
    "^charging_balance_orders$",
)

show_purchase_orders_handler = CallbackQueryHandler(
    show_purchase_orders,
    "^purchase_orders$",
)

view_charging_balance_order_handler = CallbackQueryHandler(
    view_charging_balance_order,
    r"^view_charge_order_\d+$",
)

view_purchase_order_handler = CallbackQueryHandler(
    view_purchase_order,
    r"^view_purchase_order_\d+$",
)


async def show_api_purchase_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            orders = (
                s.query(models.ApiPurchaseOrder)
                .filter(models.ApiPurchaseOrder.user_id == update.effective_user.id)
                .order_by(models.ApiPurchaseOrder.created_at.desc())
                .limit(10)
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
                    f"api_order_status_{order.status.value}", order.status.value
                )
                order_text = f"#{order.id} - {escape_html(order.game_name[:15])} - {status_text}"
                order_texts.append(order_text)
                order_data.append(f"view_api_purchase_order_{order.id}")

            order_keyboard = build_keyboard(
                columns=3,
                texts=order_texts,
                buttons_data=order_data,
            )
            order_keyboard.append(build_back_button("back_to_my_orders", lang=lang))
            order_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )

            text = f"<b>{TEXTS[lang].get('api_purchase_orders', 'API Purchase Orders ⚡')}</b>\n\n{TEXTS[lang].get('select_order', 'Select an order to view:')}"
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(order_keyboard),
            )


async def view_api_purchase_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        order_id = int(update.callback_query.data.replace("view_api_purchase_order_", ""))

        with models.session_scope() as s:
            order = s.get(models.ApiPurchaseOrder, order_id)
            if not order or order.user_id != update.effective_user.id:
                await update.callback_query.answer(
                    text=TEXTS[lang]["order_not_found"],
                    show_alert=True,
                )
                return

            # Use stringify method to build order details text
            text = order.stringify(lang)

            back_buttons = [
                build_back_button("back_to_api_purchase_orders", lang=lang),
                build_back_to_home_page_button(lang=lang, is_admin=False)[0],
            ]

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )


back_to_api_purchase_orders = show_api_purchase_orders


back_to_api_purchase_orders_handler = CallbackQueryHandler(
    back_to_api_purchase_orders,
    r"^back_to_api_purchase_orders$",
)

show_api_purchase_orders_handler = CallbackQueryHandler(
    show_api_purchase_orders,
    "^api_purchase_orders$",
)

view_api_purchase_order_handler = CallbackQueryHandler(
    view_api_purchase_order,
    r"^view_api_purchase_order_\d+$",
)