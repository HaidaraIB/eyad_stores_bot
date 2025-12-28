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
from admin.games_settings.keyboards import (
    build_games_settings_keyboard,
    build_edit_game_keyboard,
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
from custom_filters import PrivateChatAndAdmin, PermissionFilter
from start import admin_command, start_command
import models

# Conversation states
GAME_NAME, GAME_CODE, GAME_DESCRIPTION = range(3)


async def games_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_games_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["games_settings_title"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


games_settings_handler = CallbackQueryHandler(
    games_settings,
    "^games_settings$|^back_to_games_settings$",
)


async def add_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button("back_to_games_settings", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_game_instruction_name"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return GAME_NAME


async def get_game_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_back_button("back_to_get_game_name", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            game_name = update.message.text.strip()
            context.user_data["new_game_name"] = game_name
            await update.message.reply_text(
                text=TEXTS[lang]["add_game_instruction_code"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_game_instruction_code"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return GAME_CODE


back_to_get_game_name = add_game


async def get_game_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_skip_button("skip_game_description", lang=lang),
            build_back_button("back_to_get_game_code", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            game_code = update.message.text.strip().lower().replace(" ", "_")
            # Check if code already exists
            with models.session_scope() as s:
                existing = (
                    s.query(models.Game).filter(models.Game.code == game_code).first()
                )
                if existing:
                    await update.message.reply_text(
                        text=TEXTS[lang]["game_code_exists"].format(code=game_code)
                    )
                    return GAME_CODE

            context.user_data["new_game_code"] = game_code
            await update.message.reply_text(
                text=TEXTS[lang]["add_game_instruction_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_game_instruction_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return GAME_DESCRIPTION


back_to_get_game_code = get_game_name


async def skip_game_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_name = context.user_data.get("new_game_name")
        game_code = context.user_data.get("new_game_code")

        with models.session_scope() as s:
            new_game = models.Game(
                name=game_name,
                code=game_code,
                description=None,
                is_active=True,
            )
            s.add(new_game)
            s.commit()

        # Clean up user_data
        context.user_data.pop("new_game_name", None)
        context.user_data.pop("new_game_code", None)

        await update.callback_query.answer(
            text=TEXTS[lang]["game_added_success"],
            show_alert=True,
        )
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


async def get_game_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_description = update.message.text.strip() if update.message.text else None

        game_name = context.user_data.get("new_game_name")
        game_code = context.user_data.get("new_game_code")

        with models.session_scope() as s:
            new_game = models.Game(
                name=game_name,
                code=game_code,
                description=game_description,
                is_active=True,
            )
            s.add(new_game)
            s.commit()

        # Clean up user_data
        context.user_data.pop("new_game_name", None)
        context.user_data.pop("new_game_code", None)

        await update.message.reply_text(
            text=TEXTS[lang]["game_added_success"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


add_game_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_game,
            "^add_game$",
        ),
    ],
    states={
        GAME_NAME: [
            MessageHandler(
                callback=get_game_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        GAME_CODE: [
            MessageHandler(
                callback=get_game_code,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        GAME_DESCRIPTION: [
            MessageHandler(
                callback=get_game_description,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(skip_game_description, r"^skip_game_description$"),
        ],
    },
    fallbacks=[
        games_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_get_game_code, r"^back_to_get_game_code$"),
        CallbackQueryHandler(back_to_get_game_name, r"^back_to_get_game_name$"),
    ],
)


CHOOSE_GAME_TO_REMOVE = range(1)


async def remove_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            if update.callback_query.data.isnumeric():
                game = s.get(models.Game, int(update.callback_query.data))
                if game:
                    s.delete(game)
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["game_removed_success"],
                        show_alert=True,
                    )

            games = s.query(models.Game).all()

            if not games:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_games"],
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

            game_keyboard = [
                [
                    InlineKeyboardButton(
                        text=game.name,
                        callback_data=str(game.id),
                    ),
                ]
                for game in games
            ]
        game_keyboard.append(build_back_button("back_to_games_settings", lang=lang))
        game_keyboard.append(build_back_to_home_page_button(lang=lang)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["remove_game_instruction"],
            reply_markup=InlineKeyboardMarkup(game_keyboard),
        )
        return CHOOSE_GAME_TO_REMOVE


remove_game_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            remove_game,
            "^remove_game$",
        ),
    ],
    states={
        CHOOSE_GAME_TO_REMOVE: [
            CallbackQueryHandler(
                remove_game,
                r"^[0-9]+$",
            ),
        ]
    },
    fallbacks=[
        games_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
    ],
)


(
    CHOOSE_GAME_TO_EDIT,
    EDITING_GAME_NAME,
    EDITING_GAME_CODE,
    EDITING_GAME_DESCRIPTION,
    EDITING_GAME_STATUS,
) = range(5)


async def edit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            games = s.query(models.Game).all()

            if not games:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_games"], show_alert=True
                )
                return ConversationHandler.END

            game_keyboard = build_keyboard(
                columns=1,
                texts=[game.name for game in games],
                buttons_data=[str(game.id) for game in games],
            )
            game_keyboard.append(build_back_button("back_to_games_settings", lang=lang))
            game_keyboard.append(build_back_to_home_page_button(lang=lang)[0])

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_game_to_edit"],
                reply_markup=InlineKeyboardMarkup(game_keyboard),
            )
        return CHOOSE_GAME_TO_EDIT


async def show_game_edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith(
            "back"
        ) and not update.callback_query.data.startswith("toggle_game_status"):
            game_id = int(update.callback_query.data)
            context.user_data["editing_game_id"] = game_id
        else:
            game_id = context.user_data["editing_game_id"]

        keyboard = build_edit_game_keyboard(lang)
        keyboard.append(build_back_button("back_to_choose_game_to_edit", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang)[0])

        with models.session_scope() as s:
            game = s.get(models.Game, game_id)

            text = game.stringify(lang)
            text += f"\n\n{TEXTS[lang]['select_what_to_edit']}"

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return EDITING_GAME_STATUS


back_to_choose_game_to_edit = edit_game


async def handle_edit_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        action = update.callback_query.data
        game_id = context.user_data.get("editing_game_id")

        back_buttons = [
            build_back_button("back_to_handle_edit_game_action", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if action == "toggle_game_status":
            with models.session_scope() as s:
                game = s.get(models.Game, game_id)
                if game:
                    game.is_active = not game.is_active
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["game_status_updated"],
                        show_alert=True,
                    )
                    # Refresh the edit options screen
                    return await show_game_edit_options(update, context)
        elif action == "edit_game_name":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_game_name"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_GAME_NAME
        elif action == "edit_game_code":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_game_code"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_GAME_CODE
        elif action == "edit_game_description":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_game_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_GAME_DESCRIPTION


back_to_handle_edit_game_action = show_game_edit_options


async def save_game_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_id = context.user_data.get("editing_game_id")
        new_name = update.message.text.strip()

        with models.session_scope() as s:
            game = s.get(models.Game, game_id)
            if game:
                game.name = new_name

        await update.message.reply_text(
            text=TEXTS[lang]["game_name_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_game_id", None)
        return ConversationHandler.END


async def save_game_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_id = context.user_data.get("editing_game_id")
        new_code = update.message.text.strip().lower().replace(" ", "_")

        with models.session_scope() as s:
            existing = (
                s.query(models.Game)
                .filter(models.Game.code == new_code, models.Game.id != game_id)
                .first()
            )
            if existing:
                await update.message.reply_text(
                    text=TEXTS[lang]["game_code_exists"].format(code=new_code)
                )
                return EDITING_GAME_CODE

            game = s.get(models.Game, game_id)
            if game:
                game.code = new_code

        await update.message.reply_text(
            text=TEXTS[lang]["game_code_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_game_id", None)
        return ConversationHandler.END


async def save_game_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_id = context.user_data.get("editing_game_id")
        new_description = update.message.text.strip() if update.message.text else None

        with models.session_scope() as s:
            game = s.get(models.Game, game_id)
            if game:
                game.description = new_description

        await update.message.reply_text(
            text=TEXTS[lang]["game_description_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_game_id", None)
        return ConversationHandler.END


edit_game_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            edit_game,
            r"^edit_game$",
        ),
    ],
    states={
        CHOOSE_GAME_TO_EDIT: [
            CallbackQueryHandler(
                show_game_edit_options,
                r"^[0-9]+$",
            ),
        ],
        EDITING_GAME_STATUS: [
            CallbackQueryHandler(
                handle_edit_game_action,
                r"^edit_game_((name)|(code)|(description))|toggle_game_status$",
            ),
        ],
        EDITING_GAME_NAME: [
            MessageHandler(
                callback=save_game_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        EDITING_GAME_CODE: [
            MessageHandler(
                callback=save_game_code,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        EDITING_GAME_DESCRIPTION: [
            MessageHandler(
                callback=save_game_description,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
    },
    fallbacks=[
        games_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_choose_game_to_edit,
            r"^back_to_choose_game_to_edit$",
        ),
        CallbackQueryHandler(
            back_to_handle_edit_game_action,
            r"^back_to_handle_edit_game_action$",
        ),
    ],
)
