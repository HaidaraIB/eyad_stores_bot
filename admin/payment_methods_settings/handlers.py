from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from admin.payment_methods_settings.keyboards import (
    build_payment_methods_settings_keyboard,
    build_payment_method_type_keyboard,
    build_edit_payment_method_keyboard,
    build_payment_addresses_keyboard,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from common.keyboards import (
    build_admin_keyboard,
    build_back_to_home_page_button,
    build_back_button,
    build_keyboard,
    build_skip_button,
)
from common.lang_dicts import TEXTS, BUTTONS, get_lang
from common.common import escape_html
from custom_filters import PrivateChatAndAdmin, PermissionFilter
from start import admin_command, start_command
import models

# Conversation states for PaymentMethod
PM_NAME, PM_TYPE, PM_DESCRIPTION = range(3)
CHOOSE_PM_TO_REMOVE = range(1)


async def payment_methods_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_payment_methods_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["payment_methods_settings_title"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


payment_methods_settings_handler = CallbackQueryHandler(
    payment_methods_settings,
    "^payment_methods_settings$|^back_to_payment_methods_settings$",
)


# ========== PaymentMethod CRUD Operations ==========


async def add_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button("back_to_payment_methods_settings", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=True)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_payment_method_instruction_name"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return PM_NAME


async def get_payment_method_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        type_keyboard = build_payment_method_type_keyboard(lang)
        type_keyboard.append(build_back_button("back_to_get_pm_name", lang=lang))
        type_keyboard.append(
            build_back_to_home_page_button(lang=lang, is_admin=True)[0]
        )
        if update.message:
            pm_name = update.message.text.strip()
            context.user_data["new_pm_name"] = pm_name
            await update.message.reply_text(
                text=TEXTS[lang]["add_payment_method_instruction_type"],
                reply_markup=InlineKeyboardMarkup(type_keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_payment_method_instruction_type"],
                reply_markup=InlineKeyboardMarkup(type_keyboard),
            )

        return PM_TYPE


back_to_get_pm_name = add_payment_method


async def get_payment_method_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            pm_type_str = update.callback_query.data.replace("select_payment_type_", "")
            pm_type = models.PaymentMethodType(pm_type_str)
            context.user_data["new_pm_type"] = pm_type
        back_buttons = [
            build_skip_button("skip_pm_description", lang=lang),
            build_back_button("back_to_get_pm_type", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_payment_method_instruction_description"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return PM_DESCRIPTION


back_to_get_pm_type = get_payment_method_name


async def skip_pm_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        pm_name = context.user_data.get("new_pm_name")
        pm_type = context.user_data.get("new_pm_type")

        with models.session_scope() as s:
            new_pm = models.PaymentMethod(
                name=pm_name,
                type=pm_type,
                description=None,
                is_active=True,
            )
            s.add(new_pm)

        # Clean up user_data
        context.user_data.pop("new_pm_name", None)
        context.user_data.pop("new_pm_type", None)

        await update.callback_query.answer(
            text=TEXTS[lang]["payment_method_added_success"],
            show_alert=True,
        )
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


async def get_payment_method_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        pm_description = update.message.text.strip()
        pm_name = context.user_data.get("new_pm_name")
        pm_type = context.user_data.get("new_pm_type")

        with models.session_scope() as s:
            new_pm = models.PaymentMethod(
                name=pm_name,
                type=pm_type,
                description=pm_description,
                is_active=True,
            )
            s.add(new_pm)

        # Clean up user_data
        context.user_data.pop("new_pm_name", None)
        context.user_data.pop("new_pm_type", None)

        await update.message.reply_text(
            text=TEXTS[lang]["payment_method_added_success"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


add_payment_method_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_payment_method,
            "^add_payment_method$",
        ),
    ],
    states={
        PM_NAME: [
            MessageHandler(
                callback=get_payment_method_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        PM_TYPE: [
            CallbackQueryHandler(
                get_payment_method_type,
                r"^select_payment_type_",
            ),
        ],
        PM_DESCRIPTION: [
            MessageHandler(
                callback=get_payment_method_description,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(skip_pm_description, r"^skip_pm_description$"),
        ],
    },
    fallbacks=[
        payment_methods_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_get_pm_name, r"^back_to_get_pm_name$"),
        CallbackQueryHandler(back_to_get_pm_type, r"^back_to_get_pm_type$"),
    ],
)


CHOOSE_PM_TO_REMOVE = range(1)


async def remove_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            if update.callback_query.data.isnumeric():
                pm = s.get(models.PaymentMethod, int(update.callback_query.data))
                if pm:
                    s.delete(pm)
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["payment_method_removed_success"],
                        show_alert=True,
                    )

            payment_methods = s.query(models.PaymentMethod).all()

            if not payment_methods:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_payment_methods"],
                    show_alert=True,
                )
                if update.callback_query.data.isnumeric():
                    await update.callback_query.edit_message_text(
                        text=TEXTS[lang]["home_page"],
                        reply_markup=build_admin_keyboard(
                            lang=lang, user_id=update.effective_user.id
                        ),
                    )
                return ConversationHandler.END

            pm_keyboard = [
                [
                    InlineKeyboardButton(
                        text=pm.name,
                        callback_data=str(pm.id),
                    ),
                ]
                for pm in payment_methods
            ]
        pm_keyboard.append(
            build_back_button("back_to_payment_methods_settings", lang=lang)
        )
        pm_keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["remove_payment_method_instruction"],
            reply_markup=InlineKeyboardMarkup(pm_keyboard),
        )
        return CHOOSE_PM_TO_REMOVE


remove_payment_method_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            remove_payment_method,
            "^remove_payment_method$",
        ),
    ],
    states={
        CHOOSE_PM_TO_REMOVE: [
            CallbackQueryHandler(
                remove_payment_method,
                r"^[0-9]+$",
            ),
        ]
    },
    fallbacks=[
        payment_methods_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
    ],
)


(
    CHOOSE_PM_TO_EDIT,
    EDITING_PM_NAME,
    EDITING_PM_TYPE,
    EDITING_PM_DESCRIPTION,
    EDITING_PM_STATUS,
) = range(5)


async def edit_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            payment_methods = s.query(models.PaymentMethod).all()

            if not payment_methods:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_payment_methods"], show_alert=True
                )
                return ConversationHandler.END

            pm_keyboard = build_keyboard(
                columns=1,
                texts=[pm.name for pm in payment_methods],
                buttons_data=[str(pm.id) for pm in payment_methods],
            )
            pm_keyboard.append(
                build_back_button("back_to_payment_methods_settings", lang=lang)
            )
            pm_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_payment_method_to_edit"],
                reply_markup=InlineKeyboardMarkup(pm_keyboard),
            )
        return CHOOSE_PM_TO_EDIT


async def show_pm_edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            pm_id = int(update.callback_query.data)
            context.user_data["editing_pm_id"] = pm_id
        else:
            pm_id = context.user_data["editing_pm_id"]

        keyboard = build_edit_payment_method_keyboard(lang)
        keyboard.append(build_back_button("back_to_choose_pm_to_edit", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])

        with models.session_scope() as s:
            pm = s.get(models.PaymentMethod, pm_id)

            text = pm.stringify(lang)
            text += f"\n\n{TEXTS[lang]['select_what_to_edit']}"

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return EDITING_PM_STATUS


back_to_choose_pm_to_edit = edit_payment_method


async def handle_edit_pm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        action = update.callback_query.data
        pm_id = context.user_data.get("editing_pm_id")

        back_buttons = [
            build_back_button("back_to_handle_edit_pm_action", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if action == "toggle_payment_method_status":
            with models.session_scope() as s:
                pm = s.get(models.PaymentMethod, pm_id)
                if pm:
                    pm.is_active = not pm.is_active
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["payment_method_status_updated"],
                        show_alert=True,
                    )
                    return await show_pm_edit_options(update, context)
        elif action == "edit_payment_method_name":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_payment_method_name"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_PM_NAME
        elif action == "edit_payment_method_type":
            with models.session_scope() as s:
                pm = s.get(models.PaymentMethod, pm_id)
                type_keyboard = build_payment_method_type_keyboard(
                    lang, pm.type if pm else None
                )
                type_keyboard.append(
                    build_back_button("back_to_handle_edit_pm_action", lang=lang)
                )
                type_keyboard.append(
                    build_back_to_home_page_button(lang=lang, is_admin=True)[0]
                )
                await update.callback_query.edit_message_text(
                    text=TEXTS[lang]["select_new_payment_method_type"],
                    reply_markup=InlineKeyboardMarkup(type_keyboard),
                )
            return EDITING_PM_TYPE
        elif action == "edit_payment_method_description":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_payment_method_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_PM_DESCRIPTION


back_to_handle_edit_pm_action = show_pm_edit_options


async def save_pm_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        pm_id = context.user_data.get("editing_pm_id")
        pm_type_str = update.callback_query.data.replace("select_payment_type_", "")
        pm_type = models.PaymentMethodType(pm_type_str)
        with models.session_scope() as s:
            pm = s.get(models.PaymentMethod, pm_id)
            if pm:
                pm.type = pm_type

        await update.callback_query.answer(
            text=TEXTS[lang]["payment_method_type_updated"], show_alert=True
        )
        return await show_pm_edit_options(update, context)


async def save_pm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        pm_id = context.user_data.get("editing_pm_id")
        new_name = update.message.text.strip()

        with models.session_scope() as s:
            pm = s.get(models.PaymentMethod, pm_id)
            if pm:
                pm.name = new_name

        await update.message.reply_text(
            text=TEXTS[lang]["payment_method_name_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_pm_id", None)
        return ConversationHandler.END


async def save_pm_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        pm_id = context.user_data.get("editing_pm_id")
        new_description = update.message.text.strip()

        with models.session_scope() as s:
            pm = s.get(models.PaymentMethod, pm_id)
            if pm:
                pm.description = new_description

        await update.message.reply_text(
            text=TEXTS[lang]["payment_method_description_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_pm_id", None)
        return ConversationHandler.END


edit_payment_method_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            edit_payment_method,
            r"^edit_payment_method$",
        ),
    ],
    states={
        CHOOSE_PM_TO_EDIT: [
            CallbackQueryHandler(
                show_pm_edit_options,
                r"^[0-9]+$",
            ),
        ],
        EDITING_PM_STATUS: [
            CallbackQueryHandler(
                handle_edit_pm_action,
                r"^edit_payment_method_((name)|(type)|(description))|toggle_payment_method_status$",
            ),
        ],
        EDITING_PM_NAME: [
            MessageHandler(
                callback=save_pm_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        EDITING_PM_TYPE: [
            CallbackQueryHandler(
                save_pm_type,
                r"^select_payment_type_",
            ),
        ],
        EDITING_PM_DESCRIPTION: [
            MessageHandler(
                callback=save_pm_description,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
    },
    fallbacks=[
        payment_methods_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_choose_pm_to_edit,
            r"^back_to_choose_pm_to_edit$",
        ),
        CallbackQueryHandler(
            back_to_handle_edit_pm_action,
            r"^back_to_handle_edit_pm_action$",
        ),
    ],
)


# ========== PaymentMethodAddress Management ==========

(
    CHOOSE_PM_FOR_ADDRESS,
    ADDRESS_LABEL,
    ADDRESS_VALUE,
    ADDRESS_ACCOUNT_NAME,
    ADDRESS_ADDITIONAL_INFO,
) = range(5)


async def manage_payment_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            payment_methods = s.query(models.PaymentMethod).all()

            if not payment_methods:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_payment_methods"], show_alert=True
                )
                return ConversationHandler.END

            pm_keyboard = build_keyboard(
                columns=1,
                texts=[pm.name for pm in payment_methods],
                buttons_data=[f"manage_addresses_{pm.id}" for pm in payment_methods],
            )
            pm_keyboard.append(
                build_back_button("back_to_payment_methods_settings", lang=lang)
            )
            pm_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_payment_method_for_addresses"],
                reply_markup=InlineKeyboardMarkup(pm_keyboard),
            )
        return CHOOSE_PM_FOR_ADDRESS


async def show_payment_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if update.callback_query.data.startswith("manage_addresses_"):
            pm_id = int(update.callback_query.data.replace("manage_addresses_", ""))
            context.user_data["managing_pm_id"] = pm_id
        else:
            pm_id = context.user_data.get("managing_pm_id")

        with models.session_scope() as s:
            pm = s.get(models.PaymentMethod, pm_id)
            addresses = (
                s.query(models.PaymentMethodAddress)
                .filter(models.PaymentMethodAddress.payment_method_id == pm_id)
                .order_by(models.PaymentMethodAddress.priority)
                .all()
            )

            keyboard = build_payment_addresses_keyboard(pm_id, lang)
            keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])

            text = pm.stringify(lang)
            text += f"\n\n<b>{TEXTS[lang]['payment_addresses_management']}</b>"
            text += f"\n{TEXTS[lang]['addresses_count']}: <code>{len(addresses)}</code>"

            if addresses:
                address_label = TEXTS[lang].get("address", "Address")
                text += f"\n\n<b>{TEXTS[lang].get('addresses', 'Addresses')}:</b>"
                for idx, addr in enumerate(addresses, 1):
                    label = addr.label if addr.label else f"{address_label} #{addr.id}"
                    text += f"\n{idx}. <b>{escape_html(label)}</b> - <code>{escape_html(addr.address)}</code>"

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return ConversationHandler.END


manage_payment_addresses_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            manage_payment_addresses,
            r"^manage_payment_addresses$",
        ),
    ],
    states={
        CHOOSE_PM_FOR_ADDRESS: [
            CallbackQueryHandler(
                show_payment_addresses,
                r"^manage_addresses_\d+$",
            ),
        ],
    },
    fallbacks=[
        payment_methods_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
    ],
)

# Conversation states for PaymentMethodAddress addition
# Note: ADDRESS_LABEL, ADDRESS_VALUE, etc. are already defined above


async def add_payment_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        # Extract payment method ID from callback data
        pm_id = int(update.callback_query.data.replace("add_payment_address_", ""))
        context.user_data["adding_address_pm_id"] = pm_id

        back_buttons = [
            build_skip_button("skip_address_label", lang=lang),
            build_back_button("back_to_manage_payment_addresses", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=True)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_payment_address_instruction_label"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ADDRESS_LABEL


back_to_manage_payment_addresses = show_payment_addresses


async def get_address_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if update.message:
            label = update.message.text.strip() if update.message.text.strip() else None
            context.user_data["new_address_label"] = label
        else:
            context.user_data["new_address_label"] = None

        back_buttons = [
            build_back_button("back_to_get_address_label", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            await update.message.reply_text(
                text=TEXTS[lang]["add_payment_address_instruction_address"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_payment_address_instruction_address"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return ADDRESS_VALUE


back_to_get_address_label = add_payment_address


async def skip_address_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        context.user_data["new_address_label"] = None

        back_buttons = [
            build_back_button("back_to_get_address_value", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_payment_address_instruction_address"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ADDRESS_VALUE


async def get_address_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if update.message:
            address = update.message.text.strip()
            if not address:
                await update.message.reply_text(
                    text=TEXTS[lang]["add_payment_address_instruction_address"],
                )
                return ADDRESS_VALUE
            context.user_data["new_address_value"] = address

        back_buttons = [
            build_skip_button("skip_address_account_name", lang=lang),
            build_back_button("back_to_get_address_value", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            await update.message.reply_text(
                text=TEXTS[lang]["add_payment_address_instruction_account_name"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_payment_address_instruction_account_name"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return ADDRESS_ACCOUNT_NAME


back_to_get_address_value = get_address_label


async def get_address_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        # If called from callback query (back button), show the account name input again
        if update.callback_query and not update.message:
            back_buttons = [
                build_skip_button("skip_address_account_name", lang=lang),
                build_back_button("back_to_get_address_account_name", lang=lang),
                build_back_to_home_page_button(lang=lang)[0],
            ]
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_payment_address_instruction_account_name"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return ADDRESS_ACCOUNT_NAME

        if update.message:
            account_name = (
                update.message.text.strip() if update.message.text.strip() else None
            )
            context.user_data["new_address_account_name"] = account_name
        else:
            context.user_data["new_address_account_name"] = None

        back_buttons = [
            build_skip_button("skip_address_additional_info", lang=lang),
            build_back_button("back_to_get_address_additional_info", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            await update.message.reply_text(
                text=TEXTS[lang]["add_payment_address_instruction_additional_info"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_payment_address_instruction_additional_info"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return ADDRESS_ADDITIONAL_INFO


back_to_get_address_account_name = get_address_value


async def skip_address_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        context.user_data["new_address_account_name"] = None

        back_buttons = [
            build_skip_button("skip_address_additional_info", lang=lang),
            build_back_button("back_to_get_address_additional_info", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_payment_address_instruction_additional_info"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ADDRESS_ADDITIONAL_INFO


async def skip_address_additional_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        # Set additional_info to None and proceed to save
        additional_info = None
        pm_id = context.user_data.get("adding_address_pm_id")
        label = context.user_data.get("new_address_label")
        address = context.user_data.get("new_address_value")
        account_name = context.user_data.get("new_address_account_name")

        # Get the highest priority and add 1
        with models.session_scope() as s:
            max_priority = (
                s.query(models.PaymentMethodAddress)
                .filter(models.PaymentMethodAddress.payment_method_id == pm_id)
                .order_by(models.PaymentMethodAddress.priority.desc())
                .first()
            )
            priority = (max_priority.priority + 1) if max_priority else 0

            new_address = models.PaymentMethodAddress(
                payment_method_id=pm_id,
                label=label,
                address=address,
                account_name=account_name,
                additional_info=additional_info,
                is_active=True,
                priority=priority,
            )
            s.add(new_address)

        # Clean up user_data
        context.user_data.pop("adding_address_pm_id", None)
        context.user_data.pop("new_address_label", None)
        context.user_data.pop("new_address_value", None)
        context.user_data.pop("new_address_account_name", None)

        await update.callback_query.answer(
            text=TEXTS[lang]["payment_address_added_success"],
            show_alert=True,
        )
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


async def get_address_additional_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        # If called from callback query (back button), show the keyboard again
        if update.callback_query and not update.message:
            back_buttons = [
                build_skip_button("skip_address_additional_info", lang=lang),
                build_back_button("back_to_get_address_additional_info", lang=lang),
                build_back_to_home_page_button(lang=lang)[0],
            ]
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_payment_address_instruction_additional_info"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return ADDRESS_ADDITIONAL_INFO

        if update.message:
            additional_info = (
                update.message.text.strip() if update.message.text.strip() else None
            )
        else:
            additional_info = None

        pm_id = context.user_data.get("adding_address_pm_id")
        label = context.user_data.get("new_address_label")
        address = context.user_data.get("new_address_value")
        account_name = context.user_data.get("new_address_account_name")

        # Get the highest priority and add 1
        with models.session_scope() as s:
            max_priority = (
                s.query(models.PaymentMethodAddress)
                .filter(models.PaymentMethodAddress.payment_method_id == pm_id)
                .order_by(models.PaymentMethodAddress.priority.desc())
                .first()
            )
            priority = (max_priority.priority + 1) if max_priority else 0

            new_address = models.PaymentMethodAddress(
                payment_method_id=pm_id,
                label=label,
                address=address,
                account_name=account_name,
                additional_info=additional_info,
                is_active=True,
                priority=priority,
            )
            s.add(new_address)

        # Clean up user_data
        context.user_data.pop("adding_address_pm_id", None)
        context.user_data.pop("new_address_label", None)
        context.user_data.pop("new_address_value", None)
        context.user_data.pop("new_address_account_name", None)

        await update.message.reply_text(
            text=TEXTS[lang]["payment_address_added_success"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


back_to_get_address_additional_info = get_address_account_name


add_payment_address_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_payment_address,
            r"^add_payment_address_\d+$",
        ),
    ],
    states={
        ADDRESS_LABEL: [
            MessageHandler(
                callback=get_address_label,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(skip_address_label, r"^skip_address_label$"),
        ],
        ADDRESS_VALUE: [
            MessageHandler(
                callback=get_address_value,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        ADDRESS_ACCOUNT_NAME: [
            MessageHandler(
                callback=get_address_account_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(
                skip_address_account_name, r"^skip_address_account_name$"
            ),
        ],
        ADDRESS_ADDITIONAL_INFO: [
            MessageHandler(
                callback=get_address_additional_info,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(
                skip_address_additional_info, r"^skip_address_additional_info$"
            ),
        ],
    },
    fallbacks=[
        payment_methods_settings_handler,
        manage_payment_addresses_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_get_address_label, r"^back_to_get_address_label$"),
        CallbackQueryHandler(back_to_get_address_value, r"^back_to_get_address_value$"),
        CallbackQueryHandler(
            back_to_get_address_account_name, r"^back_to_get_address_account_name$"
        ),
        CallbackQueryHandler(
            back_to_get_address_additional_info,
            r"^back_to_get_address_additional_info$",
        ),
        CallbackQueryHandler(
            back_to_manage_payment_addresses,
            r"^back_to_manage_payment_addresses$",
        ),
    ],
)

# Conversation states for PaymentMethodAddress removal
CHOOSE_ADDRESS_TO_REMOVE = range(1)


async def remove_payment_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_PAYMENT_METHODS
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        with models.session_scope() as s:
            # Check if this is an address selection (numeric) or entry point
            if update.callback_query.data.isnumeric():
                # Address selected for removal
                address_id = int(update.callback_query.data)
                address = s.get(models.PaymentMethodAddress, address_id)
                pm_id = context.user_data.get("removing_address_pm_id")

                if address:
                    pm_id = address.payment_method_id
                    s.delete(address)
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["payment_address_removed_success"],
                        show_alert=True,
                    )
            else:
                # Entry point: extract payment method ID from callback data
                pm_id = int(
                    update.callback_query.data.replace("remove_payment_address_", "")
                )
                context.user_data["removing_address_pm_id"] = pm_id

            # Get addresses for the payment method
            addresses = (
                s.query(models.PaymentMethodAddress)
                .filter(models.PaymentMethodAddress.payment_method_id == pm_id)
                .order_by(models.PaymentMethodAddress.priority)
                .all()
            )

            if not addresses:
                context.user_data.pop("removing_address_pm_id", None)
                if update.callback_query.data.isnumeric():
                    await update.callback_query.edit_message_text(
                        text=TEXTS[lang]["home_page"],
                        reply_markup=build_admin_keyboard(
                            lang=lang, user_id=update.effective_user.id
                        ),
                    )
                else:
                    await update.callback_query.answer(
                        text=TEXTS[lang]["no_payment_addresses"],
                        show_alert=True,
                    )
                return ConversationHandler.END

            address_keyboard = build_keyboard(
                columns=1,
                texts=[
                    address.label if address.label else address.address
                    for address in addresses
                ],
                buttons_data=[str(address.id) for address in addresses],
            )
            address_keyboard.append(
                build_back_button("back_to_manage_payment_addresses", lang=lang)
            )
            address_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            pm = s.get(models.PaymentMethod, pm_id)
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["remove_payment_address_instruction"].format(
                    pm_name=pm.name if pm else "N/A"
                ),
                reply_markup=InlineKeyboardMarkup(address_keyboard),
            )
        return CHOOSE_ADDRESS_TO_REMOVE


remove_payment_address_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            remove_payment_address,
            r"^remove_payment_address_\d+$",
        ),
    ],
    states={
        CHOOSE_ADDRESS_TO_REMOVE: [
            CallbackQueryHandler(
                remove_payment_address,
                r"^\d+$",
            ),
        ],
    },
    fallbacks=[
        payment_methods_settings_handler,
        manage_payment_addresses_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_manage_payment_addresses,
            r"^back_to_manage_payment_addresses$",
        ),
    ],
)
