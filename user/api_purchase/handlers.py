from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.keyboards import build_user_keyboard
from common.lang_dicts import TEXTS, get_lang
from common.back_to_home_page import back_to_user_home_page_handler
from common.common import escape_html, format_float, get_exchange_rate
from custom_filters import PrivateChat
from start import start_command, admin_command
from services.g2bulk_api import G2BulkAPI
from user.api_purchase.keyboards import (
    build_game_keyboard,
    build_denomination_keyboard,
    build_server_keyboard,
    build_player_id_keyboard,
    build_search_results_keyboard,
    filter_active_games,
)
import models

# Conversation states for instant purchase
(
    INSTANT_PURCHASE_GAME,
    INSTANT_PURCHASE_DENOMINATION,
    INSTANT_PURCHASE_PLAYER_ID,
    INSTANT_PURCHASE_SERVER_ID,
) = range(4)


async def instant_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for instant purchase flow"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        try:
            api = G2BulkAPI()
            api_games = await api.get_games()

            if not api_games:
                await update.callback_query.answer(
                    text=TEXTS[lang].get("no_games_available", "No games available"),
                    show_alert=True,
                )
                return ConversationHandler.END

            # Filter to only show active filtered games
            games = filter_active_games(api_games)

            if not games:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "no_games_available", "No games available at the moment ❗️"
                    ),
                    show_alert=True,
                )
                return ConversationHandler.END

            # Store filtered games in context for pagination
            context.user_data["api_all_games"] = games
            context.user_data["api_games_page"] = 0

            search_hint = TEXTS[lang].get(
                "search_game_hint",
                "\n\n💡 يمكنك أيضاً كتابة اسم اللعبة للبحث عنها\n💡 You can also type the game name to search",
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get(
                    "select_game_api", "Select game for instant purchase:"
                )
                + search_hint,
                reply_markup=build_game_keyboard(games, lang, page=0),
            )
            return INSTANT_PURCHASE_GAME
        except Exception as e:
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Error connecting to service"),
                show_alert=True,
            )
            return ConversationHandler.END


async def get_instant_purchase_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection and show denominations, or pagination"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)

        # Handle search results pagination
        if update.callback_query.data.startswith("api_search_page_"):
            page_str = update.callback_query.data.replace("api_search_page_", "")
            if page_str == "info":
                await update.callback_query.answer()
                return INSTANT_PURCHASE_GAME

            try:
                page = int(page_str)
                search_results = context.user_data.get("api_search_results", [])

                if not search_results:
                    await update.callback_query.answer(
                        text=TEXTS[lang].get(
                            "api_error", "Error connecting to service"
                        ),
                        show_alert=True,
                    )
                    return INSTANT_PURCHASE_GAME

                from user.api_purchase.keyboards import SEARCH_RESULTS_PER_PAGE

                total_pages = (
                    len(search_results) + SEARCH_RESULTS_PER_PAGE - 1
                ) // SEARCH_RESULTS_PER_PAGE
                page = max(0, min(page, total_pages - 1))
                context.user_data["api_search_page"] = page

                results_count = len(search_results)
                if lang == models.Language.ARABIC:
                    results_text = f"🔍 تم العثور على {results_count} نتائج:\nاختر اللعبة من القائمة:"
                else:
                    results_text = f"🔍 Found {results_count} results:\nSelect a game from the list:"

                await update.callback_query.edit_message_text(
                    text=results_text,
                    reply_markup=build_search_results_keyboard(
                        search_results, lang, page=page
                    ),
                )
                return INSTANT_PURCHASE_GAME
            except (ValueError, IndexError):
                await update.callback_query.answer(
                    text=TEXTS[lang].get("api_error", "Error connecting to service"),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_GAME

        # Handle games pagination
        if update.callback_query.data.startswith("api_games_page_"):
            page_str = update.callback_query.data.replace("api_games_page_", "")
            if page_str == "info":
                # Just show current page info, don't change page
                await update.callback_query.answer()
                return INSTANT_PURCHASE_GAME

            try:
                page = int(page_str)
                games = context.user_data.get("api_all_games", [])

                if not games:
                    # Reload games if not in context
                    api = G2BulkAPI()
                    api_games = await api.get_games()
                    # Filter to only show active filtered games
                    games = filter_active_games(api_games)
                    context.user_data["api_all_games"] = games

                total_pages = (len(games) + 6 - 1) // 6  # GAMES_PER_PAGE = 6
                page = max(0, min(page, total_pages - 1))  # Clamp page number
                context.user_data["api_games_page"] = page

                search_hint = TEXTS[lang].get(
                    "search_game_hint",
                    "\n\n💡 يمكنك أيضاً كتابة اسم اللعبة للبحث عنها\n💡 You can also type the game name to search",
                )

                await update.callback_query.edit_message_text(
                    text=TEXTS[lang].get(
                        "select_game_api", "Select game for instant purchase:"
                    )
                    + search_hint,
                    reply_markup=build_game_keyboard(games, lang, page=page),
                )
                return INSTANT_PURCHASE_GAME
            except (ValueError, IndexError):
                await update.callback_query.answer(
                    text=TEXTS[lang].get("api_error", "Error connecting to service"),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_GAME

        # Handle game selection
        if not update.callback_query.data.startswith("back"):
            game_code = update.callback_query.data.replace("api_game_", "")
            # Validate that the game is an active filtered game
            with models.session_scope() as s:
                api_game = (
                    s.query(models.ApiGame)
                    .filter(
                        models.ApiGame.api_game_code == game_code,
                        models.ApiGame.is_active == True,
                    )
                    .first()
                )
                if not api_game:
                    await update.callback_query.answer(
                        text=TEXTS[lang].get(
                            "game_not_available", "This game is not available"
                        ),
                        show_alert=True,
                    )
                    return INSTANT_PURCHASE_GAME
            context.user_data["api_game_code"] = game_code
        else:
            game_code = context.user_data.get("api_game_code")

        if not game_code:
            return INSTANT_PURCHASE_GAME

        try:
            api = G2BulkAPI()

            # Get game info and catalogue
            catalogue_data = await api.get_game_catalogue(game_code)
            game_info = catalogue_data.get("game", {})
            catalogues = catalogue_data.get("catalogues", [])

            if not catalogues:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "no_denominations_available", "No denominations available"
                    ),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_GAME

            # Get display name using ApiGame if available
            lang = get_lang(update.effective_user.id)
            default_name = game_info.get("name", game_code)
            with models.session_scope() as s:
                api_game = (
                    s.query(models.ApiGame)
                    .filter(
                        models.ApiGame.api_game_code == game_code,
                        models.ApiGame.is_active == True,
                    )
                    .first()
                )
                if api_game:
                    display_name = api_game.get_display_name(lang)
                else:
                    display_name = default_name

            # Store game info in context
            context.user_data["api_game_name"] = display_name
            context.user_data["api_catalogues"] = catalogues
            context.user_data["api_denoms_page"] = 0

            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get("select_denomination", "Select denomination:"),
                reply_markup=build_denomination_keyboard(catalogues, lang, page=0),
            )
            return INSTANT_PURCHASE_DENOMINATION
        except Exception as e:
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Error connecting to service"),
                show_alert=True,
            )
            return INSTANT_PURCHASE_GAME


def search_games(games: list, query: str, lang: models.Language = None) -> list:
    """Search games by name (case-insensitive, partial match)
    Searches in original name, code, and Arabic name if available"""
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    # Get all active filtered games with their Arabic names for search
    api_games_dict = {}
    if lang:
        with models.session_scope() as s:
            api_games_dict = {
                game.api_game_code: game
                for game in s.query(models.ApiGame)
                .filter(models.ApiGame.is_active == True)
                .all()
            }

    results = []
    for game in games:
        game_name = game.get("name", "").lower()
        game_code = game.get("code", "").lower()

        # Check if query matches original game name or code
        matches = query_lower in game_name or query_lower in game_code

        # Also check Arabic name if available
        if not matches and lang and game_code in api_games_dict:
            api_game = api_games_dict[game_code]
            if api_game.arabic_name:
                arabic_name_lower = api_game.arabic_name.lower()
                if query_lower in arabic_name_lower:
                    matches = True

        if matches:
            results.append(game)

    return results


async def handle_game_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text message for game search"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        search_query = update.message.text.strip()

        # Get games from context or reload
        games = context.user_data.get("api_all_games", [])
        if not games:
            try:
                api = G2BulkAPI()
                api_games = await api.get_games()
                # Filter to only show active filtered games
                games = filter_active_games(api_games)
                context.user_data["api_all_games"] = games
            except Exception:
                await update.message.reply_text(
                    text=TEXTS[lang].get("api_error", "Error connecting to service"),
                )
                return INSTANT_PURCHASE_GAME

        # Search for games (already filtered)
        search_results = search_games(games, search_query, lang)

        if not search_results:
            # No results found
            if lang == models.Language.ARABIC:
                no_results_text = f"❌ لم يتم العثور على نتائج للبحث: '{search_query}'\n\n💡 جرب البحث مرة أخرى أو اختر من القائمة"
            else:
                no_results_text = f"❌ No results found for: '{search_query}'\n\n💡 Try searching again or select from the list"

            await update.message.reply_text(
                text=no_results_text,
            )
            return INSTANT_PURCHASE_GAME

        if len(search_results) == 1:
            # Single result - proceed directly
            game = search_results[0]
            game_code = game.get("code")

            # Validate that the game is an active filtered game
            with models.session_scope() as s:
                api_game = (
                    s.query(models.ApiGame)
                    .filter(
                        models.ApiGame.api_game_code == game_code,
                        models.ApiGame.is_active == True,
                    )
                    .first()
                )
                if not api_game:
                    await update.message.reply_text(
                        text=TEXTS[lang].get(
                            "game_not_available", "This game is not available"
                        ),
                    )
                    return INSTANT_PURCHASE_GAME

            context.user_data["api_game_code"] = game_code

            try:
                api = G2BulkAPI()

                # Get game info and catalogue
                catalogue_data = await api.get_game_catalogue(game_code)
                game_info = catalogue_data.get("game", {})
                catalogues = catalogue_data.get("catalogues", [])

                if not catalogues:
                    await update.message.reply_text(
                        text=TEXTS[lang].get(
                            "no_denominations_available", "No denominations available"
                        ),
                    )
                    return INSTANT_PURCHASE_GAME

                # Store game info in context
                context.user_data["api_game_name"] = game_info.get("name", game_code)
                context.user_data["api_catalogues"] = catalogues
                context.user_data["api_denoms_page"] = 0

                await update.message.reply_text(
                    text=TEXTS[lang].get("select_denomination", "Select denomination:"),
                    reply_markup=build_denomination_keyboard(catalogues, lang, page=0),
                )
                return INSTANT_PURCHASE_DENOMINATION
            except Exception as e:
                await update.message.reply_text(
                    text=TEXTS[lang].get("api_error", "Error connecting to service"),
                )
                return INSTANT_PURCHASE_GAME
        else:
            # Multiple results - show keyboard with pagination
            results_count = len(search_results)
            context.user_data["api_search_results"] = search_results
            context.user_data["api_search_page"] = 0

            if lang == models.Language.ARABIC:
                results_text = (
                    f"🔍 تم العثور على {results_count} نتائج:\nاختر اللعبة من القائمة:"
                )
            else:
                results_text = (
                    f"🔍 Found {results_count} results:\nSelect a game from the list:"
                )

            await update.message.reply_text(
                text=results_text,
                reply_markup=build_search_results_keyboard(
                    search_results, lang, page=0
                ),
            )
            return INSTANT_PURCHASE_GAME


async def back_to_api_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to games list (first page)"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        games = context.user_data.get("api_all_games", [])

        if not games:
            # Reload games if not in context
            try:
                api = G2BulkAPI()
                games = await api.get_games()
                context.user_data["api_all_games"] = games
            except Exception:
                return await instant_purchase(update, context)

        context.user_data["api_games_page"] = 0

        search_hint = TEXTS[lang].get(
            "search_game_hint",
            "\n\n💡 يمكنك أيضاً كتابة اسم اللعبة للبحث عنها\n💡 You can also type the game name to search",
        )

        await update.callback_query.edit_message_text(
            text=TEXTS[lang].get("select_game_api", "Select game for instant purchase:")
            + search_hint,
            reply_markup=build_game_keyboard(games, lang, page=0),
        )
        return INSTANT_PURCHASE_GAME


async def get_instant_purchase_denomination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle denomination selection and get required fields, or pagination"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)

        # Handle pagination
        if update.callback_query.data.startswith("api_denoms_page_"):
            page_str = update.callback_query.data.replace("api_denoms_page_", "")
            if page_str == "info":
                # Just show current page info, don't change page
                await update.callback_query.answer()
                return INSTANT_PURCHASE_DENOMINATION

            try:
                page = int(page_str)
                catalogues = context.user_data.get("api_catalogues", [])

                if not catalogues:
                    await update.callback_query.answer(
                        text=TEXTS[lang].get(
                            "api_error", "Error connecting to service"
                        ),
                        show_alert=True,
                    )
                    return INSTANT_PURCHASE_DENOMINATION

                from user.api_purchase.keyboards import DENOMINATIONS_PER_PAGE

                total_pages = (
                    len(catalogues) + DENOMINATIONS_PER_PAGE - 1
                ) // DENOMINATIONS_PER_PAGE
                page = max(0, min(page, total_pages - 1))  # Clamp page number
                context.user_data["api_denoms_page"] = page

                await update.callback_query.edit_message_text(
                    text=TEXTS[lang].get("select_denomination", "Select denomination:"),
                    reply_markup=build_denomination_keyboard(
                        catalogues, lang, page=page
                    ),
                )
                return INSTANT_PURCHASE_DENOMINATION
            except (ValueError, IndexError):
                await update.callback_query.answer(
                    text=TEXTS[lang].get("api_error", "Error connecting to service"),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_DENOMINATION

        # Handle denomination selection
        if not update.callback_query.data.startswith("back"):
            denom_index = int(update.callback_query.data.replace("api_denom_", ""))
            catalogues = context.user_data.get("api_catalogues", [])

            if denom_index >= len(catalogues):
                await update.callback_query.answer(
                    text=TEXTS[lang].get("api_error", "Error connecting to service"),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_DENOMINATION

            selected_denom = catalogues[denom_index]
            context.user_data["api_selected_denom"] = selected_denom
        else:
            selected_denom = context.user_data.get("api_selected_denom")

        if not selected_denom:
            return INSTANT_PURCHASE_DENOMINATION

        try:
            api = G2BulkAPI()
            game_code = context.user_data.get("api_game_code")

            # Check if server is required
            servers = await api.get_game_servers(game_code)
            context.user_data["api_requires_server"] = servers is not None
            context.user_data["api_servers"] = servers

            denom_price_usd = float(selected_denom.get("amount", 0))

            # Get exchange rate
            exchange_rate = get_exchange_rate()

            # Convert price to Sudan currency for display
            denom_price_sudan = denom_price_usd * exchange_rate

            # Check user balance from database first (in Sudan currency)
            with models.session_scope() as session:
                user = session.get(models.User, update.effective_user.id)
                user_balance_sudan = float(user.balance) if user else 0.0

            if user_balance_sudan < denom_price_sudan:
                await update.callback_query.answer(
                    text=TEXTS[lang]
                    .get(
                        "insufficient_balance_charge",
                        "Insufficient balance ❌\nYour current balance: {balance} SDG\nRequired price: {price} SDG\n\nPlease charge your balance first 💰",
                    )
                    .format(
                        balance=format_float(user_balance_sudan),
                        price=format_float(denom_price_sudan),
                    ),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_DENOMINATION

            # Check API balance (API uses USD)
            user_info = await api.get_me()
            api_balance_usd = float(user_info.get("balance", 0))

            if api_balance_usd < denom_price_usd:
                await update.callback_query.answer(
                    text=TEXTS[lang].get(
                        "product_out_of_stock",
                        "This product is currently out of stock ❌\nWe apologize for the inconvenience",
                    ),
                    show_alert=True,
                )
                return INSTANT_PURCHASE_DENOMINATION

            # Check if server is required
            servers = await api.get_game_servers(game_code)
            context.user_data["api_requires_server"] = servers is not None
            context.user_data["api_servers"] = servers

            # Show product details and ask for player ID
            game_name = context.user_data.get("api_game_name", game_code)
            denom_name = selected_denom.get("name", "")

            product_details_text = (
                TEXTS[lang]
                .get(
                    "product_details_text",
                    "<b>Product Details:</b>\n\n"
                    "🎮 <b>Game:</b> {game_name}\n"
                    "📦 <b>Denomination:</b> {denomination}\n"
                    "💰 <b>Price:</b> {price}\n\n"
                    "{enter_player_id}",
                )
                .format(
                    game_name=escape_html(game_name),
                    denomination=escape_html(denom_name),
                    price=f"{format_float(denom_price_sudan)} SDG",
                    enter_player_id=TEXTS[lang].get(
                        "enter_player_id", "Enter Player ID:"
                    ),
                )
            )

            await update.callback_query.edit_message_text(
                text=product_details_text,
                reply_markup=build_player_id_keyboard(lang),
            )
            return INSTANT_PURCHASE_PLAYER_ID
        except Exception as e:
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Error connecting to service"),
                show_alert=True,
            )
            return INSTANT_PURCHASE_DENOMINATION


back_to_api_denom = get_instant_purchase_game


async def get_instant_purchase_player_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle player ID input and validate it"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)

        player_id = update.message.text.strip()
        context.user_data["api_player_id"] = player_id

        try:
            api = G2BulkAPI()
            game_code = context.user_data.get("api_game_code")
            requires_server = context.user_data.get("api_requires_server", False)

            # Validate player ID
            validation_msg = await update.message.reply_text(
                text=TEXTS[lang].get("validating_player_id", "Validating player ID..."),
            )

            if requires_server:
                # Need server ID first
                servers = context.user_data.get("api_servers", {})
                if servers:
                    await validation_msg.delete()
                    await update.message.reply_text(
                        text=TEXTS[lang].get("enter_server_id", "Enter Server ID:"),
                        reply_markup=build_server_keyboard(servers, lang),
                    )
                    return INSTANT_PURCHASE_SERVER_ID
                else:
                    # No servers available, proceed without server
                    await validation_msg.delete()
                    await update.message.reply_text(
                        text=TEXTS[lang].get(
                            "server_not_required", "This game does not require a server"
                        ),
                    )
                    # Proceed to create order
                    return await create_api_order(update, context)
            else:
                # Validate player ID without server
                try:
                    check_result = await api.check_player_id(game_code, player_id)
                    if check_result.get("valid") == "valid":
                        player_name = check_result.get("name", "N/A")
                        await validation_msg.edit_text(
                            text=TEXTS[lang]
                            .get(
                                "player_id_valid",
                                "Player ID validated ✅\nName: {player_name}",
                            )
                            .format(player_name=escape_html(player_name)),
                        )
                        # Proceed to create order
                        return await create_api_order(update, context)
                    else:
                        await validation_msg.edit_text(
                            text=TEXTS[lang].get(
                                "player_id_invalid", "Invalid player ID ❌"
                            ),
                        )
                        return INSTANT_PURCHASE_PLAYER_ID
                except Exception as e:
                    await validation_msg.edit_text(
                        text=TEXTS[lang].get(
                            "player_id_invalid", "Invalid player ID ❌"
                        ),
                    )
                    return INSTANT_PURCHASE_PLAYER_ID
        except Exception as e:
            await update.message.reply_text(
                text=TEXTS[lang].get("api_error", "Error connecting to service"),
            )
            return INSTANT_PURCHASE_PLAYER_ID


back_to_api_player_id = get_instant_purchase_denomination


async def get_instant_purchase_server_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle server ID selection and validate player ID"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)

        if update.callback_query.data.startswith("back"):
            # Go back to player ID input
            await update.callback_query.edit_message_text(
                text=TEXTS[lang].get("enter_player_id", "Enter Player ID:"),
                reply_markup=build_player_id_keyboard(lang),
            )
            return INSTANT_PURCHASE_PLAYER_ID

        # Get selected server
        server_key = update.callback_query.data.replace("api_server_", "")
        servers = context.user_data.get("api_servers", {})
        server_id = servers.get(server_key)
        context.user_data["api_server_id"] = server_id

        try:
            api = G2BulkAPI()
            game_code = context.user_data.get("api_game_code")
            player_id = context.user_data.get("api_player_id")

            # Validate player ID with server
            validation_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=TEXTS[lang].get("validating_player_id", "Validating player ID..."),
            )

            try:
                check_result = await api.check_player_id(
                    game_code, player_id, server_id
                )
                if check_result.get("valid") == "valid":
                    player_name = check_result.get("name", "N/A")
                    await validation_msg.edit_text(
                        text=TEXTS[lang]
                        .get(
                            "player_id_valid",
                            "Player ID validated ✅\nName: {player_name}",
                        )
                        .format(player_name=escape_html(player_name)),
                    )
                    # Proceed to create order
                    return await create_api_order(update, context)
                else:
                    await validation_msg.edit_text(
                        text=TEXTS[lang].get(
                            "player_id_invalid", "Invalid player ID ❌"
                        ),
                    )
                    # Go back to player ID input
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=TEXTS[lang].get("enter_player_id", "Enter Player ID:"),
                        reply_markup=build_player_id_keyboard(lang),
                    )
                    return INSTANT_PURCHASE_PLAYER_ID
            except Exception as e:
                await validation_msg.edit_text(
                    text=TEXTS[lang].get("player_id_invalid", "Invalid player ID ❌"),
                )
                # Go back to player ID input
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=TEXTS[lang].get("enter_player_id", "Enter Player ID:"),
                    reply_markup=build_player_id_keyboard(lang),
                )
                return INSTANT_PURCHASE_PLAYER_ID
        except Exception as e:
            await update.callback_query.answer(
                text=TEXTS[lang].get("api_error", "Error connecting to service"),
                show_alert=True,
            )
            return INSTANT_PURCHASE_SERVER_ID


async def create_api_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create the order via API"""
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)

        try:
            api = G2BulkAPI()
            game_code = context.user_data.get("api_game_code")
            game_name = context.user_data.get("api_game_name", game_code)
            selected_denom = context.user_data.get("api_selected_denom", {})
            player_id = context.user_data.get("api_player_id")
            server_id = context.user_data.get("api_server_id")

            denom_name = selected_denom.get("name", "")
            denom_price_usd = float(selected_denom.get("amount", 0))

            # Get exchange rate
            exchange_rate = get_exchange_rate()

            # Convert price to Sudan currency for display
            denom_price_sudan = denom_price_usd * exchange_rate

            # Show processing message
            processing_msg = await update.message.reply_text(
                text=TEXTS[lang].get("order_processing", "Processing order..."),
            )

            # Create order
            try:
                order_data = await api.create_game_order(
                    game_code=game_code,
                    catalogue_name=denom_name,
                    player_id=player_id,
                    server_id=server_id,
                    remark=f"Order from Telegram Bot - User ID: {update.effective_user.id}",
                )
            except Exception as e:
                # Handle API errors (e.g., product out of stock, invalid data, etc.)
                error_message = str(e)
                if (
                    "out of stock" in error_message.lower()
                    or "not available" in error_message.lower()
                    or "insufficient" in error_message.lower()
                ):
                    await processing_msg.edit_text(
                        text=TEXTS[lang].get(
                            "product_out_of_stock",
                            "This product is currently out of stock ❌\nWe apologize for the inconvenience",
                        ),
                    )
                else:
                    await processing_msg.edit_text(
                        text=TEXTS[lang]
                        .get("order_created_error", "Error creating order ❌\n{error}")
                        .format(error=error_message),
                    )
                return ConversationHandler.END

            if order_data.get("success"):
                order_info = order_data.get("order", {})
                api_order_id = order_info.get("order_id")
                api_message = order_data.get("message", "")

                # Store order in database and deduct balance
                with models.session_scope() as s:
                    user = s.get(models.User, update.effective_user.id)
                    if not user:
                        await processing_msg.edit_text(
                            text=TEXTS[lang].get("error", "An error occurred ❌"),
                        )
                        return ConversationHandler.END

                    # Deduct balance in SDG (API already deducted from their balance)
                    from decimal import Decimal

                    user.balance -= Decimal(str(denom_price_sudan))

                    api_order = models.ApiPurchaseOrder(
                        user_id=update.effective_user.id,
                        api_order_id=api_order_id,
                        api_game_code=game_code,
                        denomination_name=denom_name,
                        player_id=player_id,
                        player_name=order_info.get("player_name"),
                        server_id=server_id,
                        price_usd=denom_price_usd,
                        price_sudan=denom_price_sudan,
                        status=models.ApiPurchaseOrderStatus.PENDING,
                        api_message=api_message,
                        remark=f"Order from Telegram Bot - User ID: {update.effective_user.id}",
                    )
                    s.add(api_order)
                    s.commit()  # Commit to save balance deduction

                    # Show success message
                    order_text = (
                        TEXTS[lang]
                        .get(
                            "order_created_success",
                            "Order created successfully ✅\nOrder ID: {order_id}",
                        )
                        .format(order_id=api_order_id)
                    )
                    order_details = (
                        TEXTS[lang]
                        .get(
                            "order_details",
                            (
                                "Order Details:\n"
                                "Game: {game_name}\n"
                                "Denomination: {denomination}\n"
                                "Price: {price}\n"
                                "Player ID: {player_id}\n"
                                "Current Balance: {balance}"
                            ),
                        )
                        .format(
                            game_name=escape_html(game_name),
                            denomination=escape_html(denom_name),
                            price=format_float(denom_price_sudan),
                            player_id=escape_html(player_id),
                            balance=format_float(user.balance),
                        )
                    )
                    order_text += f"\n\n{order_details}"

                await processing_msg.edit_text(
                    text=order_text,
                )
            else:
                error_msg = order_data.get(
                    "message",
                    TEXTS[lang].get("api_error", "Error connecting to service"),
                )
                # Check if error is about product availability
                if (
                    "out of stock" in error_msg.lower()
                    or "not available" in error_msg.lower()
                    or "insufficient" in error_msg.lower()
                ):
                    await processing_msg.edit_text(
                        text=TEXTS[lang].get(
                            "product_out_of_stock",
                            "This product is currently out of stock ❌\nWe apologize for the inconvenience",
                        ),
                    )
                else:
                    await processing_msg.edit_text(
                        text=TEXTS[lang]
                        .get("order_created_error", "Error creating order ❌\n{error}")
                        .format(error=error_msg),
                    )

            # Clean up user_data
            context.user_data.pop("api_game_code", None)
            context.user_data.pop("api_game_name", None)
            context.user_data.pop("api_catalogues", None)
            context.user_data.pop("api_selected_denom", None)
            context.user_data.pop("api_player_id", None)
            context.user_data.pop("api_server_id", None)
            context.user_data.pop("api_requires_server", None)
            context.user_data.pop("api_servers", None)

            # Return to home page
            await update.message.reply_text(
                text=TEXTS[lang].get("home_page", "Home Page 🔝"),
                reply_markup=build_user_keyboard(lang),
            )

        except Exception as e:
            error_msg = str(e)
            await update.message.reply_text(
                text=TEXTS[lang]
                .get("order_created_error", "Error creating order ❌\n{error}")
                .format(error=error_msg),
            )
        return ConversationHandler.END


# Conversation handler
instant_purchase_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            instant_purchase,
            r"^instant_purchase$",
        ),
    ],
    states={
        INSTANT_PURCHASE_GAME: [
            CallbackQueryHandler(
                get_instant_purchase_game,
                r"^(api_game_|api_games_page_|api_search_page_)",
            ),
            MessageHandler(
                callback=handle_game_search,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        INSTANT_PURCHASE_DENOMINATION: [
            CallbackQueryHandler(
                get_instant_purchase_denomination,
                r"^(api_denom_|api_denoms_page_)",
            ),
        ],
        INSTANT_PURCHASE_PLAYER_ID: [
            MessageHandler(
                callback=get_instant_purchase_player_id,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        INSTANT_PURCHASE_SERVER_ID: [
            CallbackQueryHandler(
                get_instant_purchase_server_id,
                r"^api_server_",
            ),
        ],
    },
    fallbacks=[
        start_command,
        admin_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_api_game, r"^back_to_api_game$"),
        CallbackQueryHandler(back_to_api_denom, r"^back_to_api_denom$"),
        CallbackQueryHandler(back_to_api_player_id, r"^back_to_api_player_id$"),
    ],
)
