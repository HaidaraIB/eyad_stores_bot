from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from admin.general_settings.keyboards import build_general_settings_keyboard
from common.keyboards import build_back_to_home_page_button, build_back_button
from common.lang_dicts import TEXTS, get_lang
from common.back_to_home_page import back_to_admin_home_page_handler
from common.common import format_float
from custom_filters import PrivateChatAndAdmin, PermissionFilter
from start import admin_command, start_command
import models

# Conversation state
SET_USD_TO_SUDAN_RATE = range(1)


async def general_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GENERAL_SETTINGS
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        keyboard = build_general_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get("general_settings_title", "General Settings ⚙️"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


general_settings_handler = CallbackQueryHandler(
    general_settings, r"^general_settings$|^back_to_general_settings$"
)


async def set_usd_to_sudan_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GENERAL_SETTINGS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button("back_to_general_settings", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=True)[0],
        ]
        with models.session_scope() as session:
            settings = session.query(models.GeneralSettings).first()
            if not settings:
                settings = models.GeneralSettings()
                session.add(settings)
                session.commit()
            if update.callback_query.data == "set_usd_to_sudan_rate":
                await update.callback_query.edit_message_text(
                    text=TEXTS[lang]
                    .get(
                        "enter_usd_to_sudan_rate",
                        "Enter USD to Sudan Currency exchange rate:",
                    )
                    .format(current_rate=format_float(settings.usd_to_sudan_rate)),
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return SET_USD_TO_SUDAN_RATE


async def handle_rate_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GENERAL_SETTINGS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        rate = float(update.message.text.strip())
        # Update or create settings
        with models.session_scope() as session:
            settings = session.query(models.GeneralSettings).first()
            settings.usd_to_sudan_rate = rate

        success_text = (
            TEXTS[lang]
            .get(
                "rate_updated_success",
                "Exchange rate updated successfully ✅\nNew rate: <code>{rate}</code>",
            )
            .format(rate=format_float(rate))
        )
        await update.message.reply_text(
            text=success_text,
        )

        keyboard = build_general_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])

        await update.message.reply_text(
            text=TEXTS[lang].get("general_settings_title", "General Settings ⚙️"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


set_usd_to_sudan_rate_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            set_usd_to_sudan_rate,
            "^set_usd_to_sudan_rate$",
        )
    ],
    states={
        SET_USD_TO_SUDAN_RATE: [
            MessageHandler(
                callback=handle_rate_input,
                filters=filters.Regex(r"^[0-9]+(\.[0-9]+)?$"),
            )
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        general_settings_handler,
        admin_command,
        start_command,
    ],
)
