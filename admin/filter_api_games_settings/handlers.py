from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from admin.filter_api_games_settings.keyboards import (
    build_filter_api_games_settings_keyboard,
    build_api_games_list_keyboard,
    build_api_game_details_keyboard,
    build_filtered_games_list_keyboard,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from common.keyboards import (
    build_admin_keyboard,
    build_back_to_home_page_button,
    build_back_button,
)
from common.lang_dicts import TEXTS, get_lang
from common.common import escape_html
from custom_filters import PrivateChatAndAdmin, PermissionFilter
from start import admin_command, start_command
from services.g2bulk_api import G2BulkAPI
import models

# Conversation states
SETTING_ARABIC_NAME = range(1)


async def filter_api_games_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for filter API games settings"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        # Clear the from_filtered_games flag when returning to settings
        context.user_data.pop("from_filtered_games", None)
        keyboard = build_filter_api_games_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get(
                "filter_api_games_settings_title", "Filter API Games Settings 🔍"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


filter_api_games_settings_handler = CallbackQueryHandler(
    filter_api_games_settings,
    "^filter_api_games_settings$|^back_to_filter_api_games_settings$",
)


async def filter_api_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch games from API and show them with status indicators"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        try:
            # Fetch games from API
            api = G2BulkAPI()
            api_games = await api.get_games()

            if not api_games:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "no_games_available", "No games available from API"
                    ),
                    show_alert=True,
                )
                return ConversationHandler.END

            # Get existing games from database
            with models.session_scope() as s:
                existing_games = {
                    game.api_game_code: game for game in s.query(models.ApiGame).all()
                }

            # Store games in context for pagination
            context.user_data["api_all_games"] = api_games
            context.user_data["api_games_page"] = 0

            # Build and show keyboard
            keyboard = build_api_games_list_keyboard(
                api_games, existing_games, lang, page=0
            )

            status_text = TEXTS[lang].get(
                "api_games_list_info",
                "🟢 = Game exists and is active\n🔴 = Game doesn't exist or is inactive",
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get(
                    "select_api_game_to_manage", "Select a game to manage:"
                )
                + f"\n\n{status_text}",
                reply_markup=keyboard,
            )
            return ConversationHandler.END
        except Exception as e:
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Error connecting to API service"),
                show_alert=True,
            )
            return ConversationHandler.END


async def handle_api_games_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination for API games list"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        page_str = update.callback_query.data.replace("api_games_filter_page_", "")
        if page_str == "info":
            await update.callback_query.answer()
            return ConversationHandler.END

        try:
            page = int(page_str)
            api_games = context.user_data.get("api_all_games", [])

            if not api_games:
                # Reload games if not in context
                api = G2BulkAPI()
                api_games = await api.get_games()
                context.user_data["api_all_games"] = api_games

            # Get existing games from database
            with models.session_scope() as s:
                existing_games = {
                    game.api_game_code: game for game in s.query(models.ApiGame).all()
                }

            total_pages = (len(api_games) + 10 - 1) // 10
            page = max(0, min(page, total_pages - 1))
            context.user_data["api_games_page"] = page

            keyboard = build_api_games_list_keyboard(
                api_games, existing_games, lang, page=page
            )

            status_text = TEXTS[lang].get(
                "api_games_list_info",
                "🟢 = Game exists and is active\n🔴 = Game doesn't exist or is inactive",
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get(
                    "select_api_game_to_manage", "Select a game to manage:"
                )
                + f"\n\n{status_text}",
                reply_markup=keyboard,
            )
        except (ValueError, IndexError):
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Error connecting to API service"),
                show_alert=True,
            )


async def show_api_game_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show details of a selected API game"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        game_code = update.callback_query.data.replace("api_game_filter_", "")

        # Get game info from API games list
        api_games = context.user_data.get("api_all_games", [])
        game_info = None
        for game in api_games:
            if game.get("code") == game_code:
                game_info = game
                break

        if not game_info:
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Game not found"),
                show_alert=True,
            )
            return ConversationHandler.END

        # Get existing game from database if exists
        with models.session_scope() as s:
            existing_game = (
                s.query(models.ApiGame)
                .filter(models.ApiGame.api_game_code == game_code)
                .first()
            )

            if existing_game:
                # Game exists in database
                text = existing_game.stringify(lang)
                has_arabic_name = True
            else:
                # Game doesn't exist - create it
                new_game = models.ApiGame(
                    api_game_code=game_code,
                    api_game_name=game_info.get("name", game_code),
                    arabic_name=None,
                    is_active=True,
                )
                s.add(new_game)
                s.commit()
                text = new_game.stringify(lang)
                has_arabic_name = True
                existing_game = new_game

        keyboard = build_api_game_details_keyboard(
            game_code, has_arabic_name, lang, from_filtered_games=False
        )

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
        )
        return ConversationHandler.END


async def set_arabic_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start conversation to set Arabic name for a game"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        game_code = update.callback_query.data.replace("set_arabic_name_", "")
        context.user_data["editing_game_code"] = game_code

        back_buttons = [
            build_back_button("back_to_set_arabic_name", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=True)[0],
        ]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get(
                "enter_arabic_name", "Enter the Arabic name for this game:"
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return SETTING_ARABIC_NAME


async def back_to_set_arabic_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back from setting Arabic name"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_code = context.user_data.get("editing_game_code")

        if game_code:
            # Reload game details
            with models.session_scope() as s:
                game = (
                    s.query(models.ApiGame)
                    .filter(models.ApiGame.api_game_code == game_code)
                    .first()
                )
                if game:
                    text = game.stringify(lang)
                    from_filtered = context.user_data.get("from_filtered_games", False)
                    keyboard = build_api_game_details_keyboard(
                        game_code, True, lang, from_filtered_games=from_filtered
                    )
                    await update.callback_query.edit_message_text(
                        text=text,
                        reply_markup=keyboard,
                    )
        return ConversationHandler.END


async def save_arabic_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the Arabic name for a game"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_code = context.user_data.get("editing_game_code")
        arabic_name = update.message.text.strip()

        if not game_code:
            await update.message.reply_text(
                text=TEXTS[lang].get("error", "An error occurred"),
            )
            return ConversationHandler.END

        with models.session_scope() as s:
            game = (
                s.query(models.ApiGame)
                .filter(models.ApiGame.api_game_code == game_code)
                .first()
            )
            if game:
                game.arabic_name = arabic_name

        context.user_data.pop("editing_game_code", None)

        await update.message.reply_text(
            text=TEXTS[lang].get(
                "arabic_name_saved", "Arabic name saved successfully ✅"
            ),
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


async def toggle_api_game_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle the active status of an API game"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        game_code = update.callback_query.data.replace("toggle_api_game_status_", "")

        with models.session_scope() as s:
            game = (
                s.query(models.ApiGame)
                .filter(models.ApiGame.api_game_code == game_code)
                .first()
            )
            if game:
                game.is_active = not game.is_active
                s.commit()

                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "api_game_status_updated", "Game status updated successfully ✅"
                    ),
                    show_alert=True,
                )

                # Refresh the game details view
                text = game.stringify(lang)
                from_filtered = context.user_data.get("from_filtered_games", False)
                keyboard = build_api_game_details_keyboard(
                    game_code, True, lang, from_filtered_games=from_filtered
                )
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                )
        return ConversationHandler.END


async def back_to_api_games_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to API games list"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        api_games = context.user_data.get("api_all_games", [])
        if not api_games:
            # Reload games if not in context
            try:
                api = G2BulkAPI()
                api_games = await api.get_games()
                context.user_data["api_all_games"] = api_games
            except Exception:
                return await filter_api_games_settings(update, context)

        # Get existing games from database
        with models.session_scope() as s:
            existing_games = {
                game.api_game_code: game for game in s.query(models.ApiGame).all()
            }

        page = context.user_data.get("api_games_page", 0)
        keyboard = build_api_games_list_keyboard(
            api_games, existing_games, lang, page=page
        )

        status_text = TEXTS[lang].get(
            "api_games_list_info",
            "🟢 = Game exists and is active\n🔴 = Game doesn't exist or is inactive",
        )

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get(
                "select_api_game_to_manage", "Select a game to manage:"
            )
            + f"\n\n{status_text}",
            reply_markup=keyboard,
        )
        return ConversationHandler.END


# Conversation handler for setting Arabic name
set_arabic_name_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            set_arabic_name,
            r"^set_arabic_name_",
        ),
    ],
    states={
        SETTING_ARABIC_NAME: [
            MessageHandler(
                callback=save_arabic_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
    },
    fallbacks=[
        filter_api_games_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_set_arabic_name, r"^back_to_set_arabic_name$"),
    ],
)

# Handler for filter API games button
filter_api_games_handler = CallbackQueryHandler(
    filter_api_games,
    r"^filter_api_games$",
)

# Handler for pagination
api_games_pagination_handler = CallbackQueryHandler(
    handle_api_games_pagination,
    r"^api_games_filter_page_",
)

# Handler for game selection
api_game_details_handler = CallbackQueryHandler(
    show_api_game_details,
    r"^api_game_filter_",
)

# Handler for toggle status
toggle_api_game_status_handler = CallbackQueryHandler(
    toggle_api_game_status,
    r"^toggle_api_game_status_",
)

# Handler for back to list
back_to_api_games_list_handler = CallbackQueryHandler(
    back_to_api_games_list,
    r"^back_to_api_games_list$",
)


async def manage_filtered_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of filtered games (games in database)"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        with models.session_scope() as s:
            filtered_games = (
                s.query(models.ApiGame).order_by(models.ApiGame.api_game_name).all()
            )

            if not filtered_games:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "no_filtered_games",
                        "No filtered games found. Please filter games from API first.",
                    ),
                    show_alert=True,
                )
                return ConversationHandler.END

            # Store only page number for pagination
            context.user_data["filtered_games_page"] = 0

            # Build and show keyboard
            keyboard = build_filtered_games_list_keyboard(filtered_games, lang, page=0)

            status_text = TEXTS[lang].get(
                "filtered_games_list_info", "🟢 = Active\n🔴 = Inactive"
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get(
                    "select_filtered_game_to_manage",
                    "Select a filtered game to manage:",
                )
                + f"\n\n{status_text}",
                reply_markup=keyboard,
            )
        return ConversationHandler.END


async def handle_filtered_games_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination for filtered games list"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        page_str = update.callback_query.data.replace("filtered_games_page_", "")
        if page_str == "info":
            await update.callback_query.answer()
            return ConversationHandler.END

        try:
            page = int(page_str)
            
            # Always read from database
            with models.session_scope() as s:
                filtered_games = (
                    s.query(models.ApiGame)
                    .order_by(models.ApiGame.api_game_name)
                    .all()
                )

            total_pages = (len(filtered_games) + 10 - 1) // 10
            page = max(0, min(page, total_pages - 1))
            context.user_data["filtered_games_page"] = page

            keyboard = build_filtered_games_list_keyboard(
                filtered_games, lang, page=page
            )

            status_text = TEXTS[lang].get(
                "filtered_games_list_info", "🟢 = Active\n🔴 = Inactive"
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get(
                    "select_filtered_game_to_manage",
                    "Select a filtered game to manage:",
                )
                + f"\n\n{status_text}",
                reply_markup=keyboard,
            )
        except (ValueError, IndexError):
            await update.callback_query.answer(
                text=TEXTS[lang].get("error", "An error occurred"),
                show_alert=True,
            )


async def show_filtered_game_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Show details of a selected filtered game"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        game_code = update.callback_query.data.replace("filtered_game_manage_", "")

        with models.session_scope() as s:
            game = (
                s.query(models.ApiGame)
                .filter(models.ApiGame.api_game_code == game_code)
                .first()
            )

            if not game:
                await update.callback_query.answer(
                    text=TEXTS[lang].get("game_not_found", "Game not found"),
                    show_alert=True,
                )
                return ConversationHandler.END

            text = game.stringify(lang)
            keyboard = build_api_game_details_keyboard(
                game_code, True, lang, from_filtered_games=True
            )

        # Store that we came from filtered games list
        context.user_data["from_filtered_games"] = True

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard,
        )
        return ConversationHandler.END


async def back_to_filtered_games_list(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Go back to filtered games list"""
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.FILTER_API_GAMES
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        # Always read from database
        with models.session_scope() as s:
            filtered_games = (
                s.query(models.ApiGame).order_by(models.ApiGame.api_game_name).all()
            )

        page = context.user_data.get("filtered_games_page", 0)
        keyboard = build_filtered_games_list_keyboard(filtered_games, lang, page=page)

        status_text = TEXTS[lang].get(
            "filtered_games_list_info", "🟢 = Active\n🔴 = Inactive"
        )

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get(
                "select_filtered_game_to_manage", "Select a filtered game to manage:"
            )
            + f"\n\n{status_text}",
            reply_markup=keyboard,
        )
        return ConversationHandler.END


# Handler for manage filtered games
manage_filtered_games_handler = CallbackQueryHandler(
    manage_filtered_games,
    r"^manage_filtered_games$",
)

# Handler for filtered games pagination
filtered_games_pagination_handler = CallbackQueryHandler(
    handle_filtered_games_pagination,
    r"^filtered_games_page_",
)

# Handler for filtered game selection
filtered_game_details_handler = CallbackQueryHandler(
    show_filtered_game_details,
    r"^filtered_game_manage_",
)

# Handler for back to filtered games list
back_to_filtered_games_list_handler = CallbackQueryHandler(
    back_to_filtered_games_list,
    r"^back_to_filtered_games_list$",
)
