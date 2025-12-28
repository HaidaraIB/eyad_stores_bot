from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from common.lang_dicts import BUTTONS, TEXTS
from common.keyboards import build_keyboard, build_back_button, build_back_to_home_page_button
import models

GAMES_PER_PAGE = 10  # Number of games per page


def build_filter_api_games_settings_keyboard(lang: models.Language = models.Language.ARABIC):
    keyboard = [
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("filter_api_games", "Filter API Games 🔍"),
                callback_data="filter_api_games",
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTONS[lang].get("manage_filtered_games", "Manage Filtered Games 📋"),
                callback_data="manage_filtered_games",
            )
        ],
    ]
    return keyboard


def build_api_games_list_keyboard(
    api_games: list,
    existing_games: dict,  # {game_code: ApiGame}
    lang: models.Language,
    page: int = 0
) -> InlineKeyboardMarkup:
    """Build keyboard for API games list with status indicators"""
    total_games = len(api_games)
    total_pages = (total_games + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE
    
    # Calculate start and end indices
    start_idx = page * GAMES_PER_PAGE
    end_idx = min(start_idx + GAMES_PER_PAGE, total_games)
    
    # Get games for current page
    page_games = api_games[start_idx:end_idx]
    
    # Build keyboard with games and status indicators
    game_keyboard = []
    for game in page_games:
        game_code = game.get("code", "")
        game_name = game.get("name", "")
        
        # Check if game exists in database
        existing_game = existing_games.get(game_code)
        
        if existing_game and existing_game.is_active:
            # Green circle for active games we have
            indicator = "🟢"
        else:
            # Red circle for games we don't have or inactive
            indicator = "🔴"
        
        button_text = f"{indicator} {game_name}"
        game_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"api_game_filter_{game_code}",
            )
        ])
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️ " + BUTTONS[lang].get("back_button", "Back"),
                    callback_data=f"api_games_filter_page_{page - 1}",
                )
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="api_games_filter_page_info",
            )
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("next_button", "Next") + " ▶️",
                    callback_data=f"api_games_filter_page_{page + 1}",
                )
            )
        
        if pagination_row:
            game_keyboard.append(pagination_row)
    
    # Add back button
    game_keyboard.append(build_back_button("back_to_filter_api_games_settings", lang=lang))
    game_keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
    
    return InlineKeyboardMarkup(game_keyboard)


def build_api_game_details_keyboard(
    game_code: str,
    has_arabic_name: bool,
    lang: models.Language,
    from_filtered_games: bool = False
) -> InlineKeyboardMarkup:
    """Build keyboard for individual API game details"""
    keyboard = []
    
    # Only show set Arabic name button if game exists in database
    if has_arabic_name:
        keyboard.append([
            InlineKeyboardButton(
                text=TEXTS[lang].get("set_arabic_name", "Set Arabic Name"),
                callback_data=f"set_arabic_name_{game_code}",
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text=TEXTS[lang].get("toggle_api_game_status", "Toggle Status"),
                callback_data=f"toggle_api_game_status_{game_code}",
            )
        ])
    
    # Use appropriate back button based on source
    if from_filtered_games:
        keyboard.append(build_back_button("back_to_filtered_games_list", lang=lang))
    else:
        keyboard.append(build_back_button("back_to_api_games_list", lang=lang))
    keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
    
    return InlineKeyboardMarkup(keyboard)


def build_filtered_games_list_keyboard(
    filtered_games: list,  # List of ApiGame objects
    lang: models.Language,
    page: int = 0
) -> InlineKeyboardMarkup:
    """Build keyboard for filtered games list (games in database)"""
    total_games = len(filtered_games)
    total_pages = (total_games + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE
    
    # Calculate start and end indices
    start_idx = page * GAMES_PER_PAGE
    end_idx = min(start_idx + GAMES_PER_PAGE, total_games)
    
    # Get games for current page
    page_games = filtered_games[start_idx:end_idx]
    
    # Build keyboard with games
    game_keyboard = []
    for game in page_games:
        # Get display name based on language
        display_name = game.get_display_name(lang)
        status_indicator = "🟢" if game.is_active else "🔴"
        
        button_text = f"{status_indicator} {display_name}"
        game_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"filtered_game_manage_{game.api_game_code}",
            )
        ])
    
    # Add pagination buttons if needed
    pagination_row = []
    if total_pages > 1:
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀️ " + BUTTONS[lang].get("back_button", "Back"),
                    callback_data=f"filtered_games_page_{page - 1}",
                )
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="filtered_games_page_info",
            )
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text=BUTTONS[lang].get("next_button", "Next") + " ▶️",
                    callback_data=f"filtered_games_page_{page + 1}",
                )
            )
        
        if pagination_row:
            game_keyboard.append(pagination_row)
    
    # Add back button
    game_keyboard.append(build_back_button("back_to_filter_api_games_settings", lang=lang))
    game_keyboard.append(build_back_to_home_page_button(lang=lang, is_admin=True)[0])
    
    return InlineKeyboardMarkup(game_keyboard)

