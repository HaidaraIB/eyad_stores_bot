from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from common.keyboards import (
    build_back_to_home_page_button,
    build_back_button,
    build_keyboard,
)
from common.lang_dicts import BUTTONS
from common.common import format_float, get_exchange_rate
import models

GAMES_PER_PAGE = 6  # Number of games per page
DENOMINATIONS_PER_PAGE = 6  # Number of denominations per page
SEARCH_RESULTS_PER_PAGE = 6  # Number of search results per page


def build_game_keyboard(
    games: list, lang: models.Language, page: int = 0
) -> InlineKeyboardMarkup:
    """Build keyboard for game selection with pagination"""
    total_games = len(games)
    total_pages = (total_games + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE
    
    # Calculate start and end indices
    start_idx = page * GAMES_PER_PAGE
    end_idx = min(start_idx + GAMES_PER_PAGE, total_games)
    
    # Get games for current page
    page_games = games[start_idx:end_idx]
    
    # Build keyboard with games
    game_keyboard = build_keyboard(
        columns=1,
        texts=[game["name"] for game in page_games],
        buttons_data=[f"api_game_{game['code']}" for game in page_games],
    )
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️ " + BUTTONS[lang].get("back_button", "Back"),
                    callback_data=f"api_games_page_{page - 1}",
                )
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="api_games_page_info",
            )
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("next_button", "Next") + " ▶️",
                    callback_data=f"api_games_page_{page + 1}",
                )
            )
        
        if pagination_row:
            game_keyboard.append(pagination_row)
    
    # Add back button
    game_keyboard.append(
        build_back_to_home_page_button(lang=lang, is_admin=False)[0]
    )
    
    return InlineKeyboardMarkup(game_keyboard)


def build_denomination_keyboard(
    catalogues: list, lang: models.Language, page: int = 0
) -> InlineKeyboardMarkup:
    """Build keyboard for denomination selection with pagination"""
    total_denoms = len(catalogues)
    total_pages = (total_denoms + DENOMINATIONS_PER_PAGE - 1) // DENOMINATIONS_PER_PAGE
    
    # Calculate start and end indices
    start_idx = page * DENOMINATIONS_PER_PAGE
    end_idx = min(start_idx + DENOMINATIONS_PER_PAGE, total_denoms)
    
    # Get denominations for current page
    page_catalogues = catalogues[start_idx:end_idx]
    
    # Get exchange rate
    exchange_rate = get_exchange_rate()
    
    # Build keyboard with denominations (convert USD to Sudan currency for display)
    denomination_keyboard = build_keyboard(
        columns=1,
        texts=[
            f"{cat['name']} - {format_float(float(cat['amount']) * exchange_rate)} SDG" 
            for cat in page_catalogues
        ],
        buttons_data=[f"api_denom_{start_idx + i}" for i in range(len(page_catalogues))],
    )
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️ " + BUTTONS[lang].get("back_button", "Back"),
                    callback_data=f"api_denoms_page_{page - 1}",
                )
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="api_denoms_page_info",
            )
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("next_button", "Next") + " ▶️",
                    callback_data=f"api_denoms_page_{page + 1}",
                )
            )
        
        if pagination_row:
            denomination_keyboard.append(pagination_row)
    
    denomination_keyboard.append(
        build_back_button("back_to_api_game", lang=lang)
    )
    denomination_keyboard.append(
        build_back_to_home_page_button(lang=lang, is_admin=False)[0]
    )
    return InlineKeyboardMarkup(denomination_keyboard)


def build_server_keyboard(servers: dict, lang: models.Language) -> InlineKeyboardMarkup:
    """Build keyboard for server selection"""
    server_keyboard = build_keyboard(
        columns=1,
        texts=list(servers.keys()),
        buttons_data=[f"api_server_{k}" for k in servers.keys()],
    )
    server_keyboard.append(
        build_back_button("back_to_api_player_id", lang=lang)
    )
    server_keyboard.append(
        build_back_to_home_page_button(lang=lang, is_admin=False)[0]
    )
    return InlineKeyboardMarkup(server_keyboard)


def build_product_details_keyboard(lang: models.Language) -> InlineKeyboardMarkup:
    """Build keyboard for product details confirmation"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("confirm_button", "Confirm ✅"),
                callback_data="api_confirm_product",
            )
        ],
        build_back_button("back_to_api_denom", lang=lang),
        build_back_to_home_page_button(lang=lang, is_admin=False)[0],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_player_id_keyboard(lang: models.Language) -> InlineKeyboardMarkup:
    """Build keyboard for player ID input"""
    back_buttons = [
        build_back_button("back_to_api_denom", lang=lang),
        build_back_to_home_page_button(lang=lang, is_admin=False)[0],
    ]
    return InlineKeyboardMarkup(back_buttons)


def build_search_results_keyboard(
    games: list, lang: models.Language, page: int = 0
) -> InlineKeyboardMarkup:
    """Build keyboard for search results with pagination"""
    total_games = len(games)
    total_pages = (total_games + SEARCH_RESULTS_PER_PAGE - 1) // SEARCH_RESULTS_PER_PAGE
    
    # Calculate start and end indices
    start_idx = page * SEARCH_RESULTS_PER_PAGE
    end_idx = min(start_idx + SEARCH_RESULTS_PER_PAGE, total_games)
    
    # Get games for current page
    page_games = games[start_idx:end_idx]
    
    # Build keyboard with games
    search_keyboard = build_keyboard(
        columns=1,
        texts=[game["name"] for game in page_games],
        buttons_data=[f"api_game_{game['code']}" for game in page_games],
    )
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️ " + BUTTONS[lang].get("back_button", "Back"),
                    callback_data=f"api_search_page_{page - 1}",
                )
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="api_search_page_info",
            )
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("next_button", "Next") + " ▶️",
                    callback_data=f"api_search_page_{page + 1}",
                )
            )
        
        if pagination_row:
            search_keyboard.append(pagination_row)
    
    search_keyboard.append(
        build_back_button("back_to_api_game", lang=lang)
    )
    search_keyboard.append(
        build_back_to_home_page_button(lang=lang, is_admin=False)[0]
    )
    return InlineKeyboardMarkup(search_keyboard)

