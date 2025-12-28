from telegram import (
    Update,
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
from admin.items_settings.keyboards import (
    build_items_settings_keyboard,
    build_item_type_keyboard,
    build_edit_item_keyboard,
)
from common.back_to_home_page import back_to_admin_home_page_handler
from common.keyboards import (
    build_admin_keyboard,
    build_back_to_home_page_button,
    build_back_button,
    build_keyboard,
    build_skip_button,
)
from common.lang_dicts import TEXTS, get_lang
from custom_filters import PrivateChatAndAdmin, PermissionFilter
from start import admin_command, start_command
import models

# Conversation states
ITEM_GAME, ITEM_NAME, ITEM_TYPE, ITEM_PRICE, ITEM_DESCRIPTION, ITEM_STOCK = range(6)


async def items_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        keyboard = build_items_settings_keyboard(lang)
        keyboard.append(build_back_to_home_page_button(lang=lang)[0])
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["items_settings_title"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


items_settings_handler = CallbackQueryHandler(
    items_settings,
    "^items_settings$|^back_to_items_settings$",
)


async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            games = s.query(models.Game).filter(models.Game.is_active == True).all()

            if not games:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_active_games"], show_alert=True
                )
                return ConversationHandler.END

            game_keyboard = build_keyboard(
                columns=1,
                texts=[game.name for game in games],
                buttons_data=[str(game.id) for game in games],
            )
            game_keyboard.append(build_back_button("back_to_items_settings", lang=lang))
            game_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=True)[0]
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_item_instruction_game"],
                reply_markup=InlineKeyboardMarkup(game_keyboard),
            )
        return ITEM_GAME


async def get_item_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            game_id = int(update.callback_query.data)
            context.user_data["new_item_game_id"] = game_id

        back_buttons = [
            build_back_button("back_to_get_item_game", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_item_instruction_name"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ITEM_NAME


back_to_get_item_game = add_item


async def get_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        type_keyboard = build_item_type_keyboard(lang)
        type_keyboard.append(build_back_button("back_to_get_item_name", lang=lang))
        type_keyboard.append(
            build_back_to_home_page_button(lang=lang, is_admin=True)[0]
        )
        if update.message:
            item_name = update.message.text.strip()
            context.user_data["new_item_name"] = item_name
            await update.message.reply_text(
                text=TEXTS[lang]["add_item_instruction_type"],
                reply_markup=InlineKeyboardMarkup(type_keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_item_instruction_type"],
                reply_markup=InlineKeyboardMarkup(type_keyboard),
            )

        return ITEM_TYPE


back_to_get_item_name = get_item_game


async def get_item_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            item_type_str = update.callback_query.data.replace("select_item_type_", "")
            item_type = models.ItemType(item_type_str)
            context.user_data["new_item_type"] = item_type

        back_buttons = [
            build_back_button("back_to_get_item_type", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_item_instruction_price"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ITEM_PRICE


back_to_get_item_type = get_item_name


async def get_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_skip_button("skip_item_description", lang=lang),
            build_back_button("back_to_get_item_price", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            item_price = float(update.message.text.strip())
            context.user_data["new_item_price"] = item_price
            await update.message.reply_text(
                text=TEXTS[lang]["add_item_instruction_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_item_instruction_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return ITEM_DESCRIPTION


back_to_get_item_price = get_item_type


async def get_item_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        back_buttons = [
            build_skip_button("skip_item_stock", lang=lang),
            build_back_button("back_to_get_item_description", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if update.message:
            item_description = update.message.text.strip()
            context.user_data["new_item_description"] = item_description
            await update.message.reply_text(
                text=TEXTS[lang]["add_item_instruction_stock"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["add_item_instruction_stock"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return ITEM_STOCK


back_to_get_item_description = get_item_price


async def skip_item_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        context.user_data["new_item_description"] = None
        
        back_buttons = [
            build_skip_button("skip_item_stock", lang=lang),
            build_back_button("back_to_get_item_description", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["add_item_instruction_stock"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return ITEM_STOCK


async def skip_item_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        game_id = context.user_data.get("new_item_game_id")
        item_name = context.user_data.get("new_item_name")
        item_type = context.user_data.get("new_item_type")
        item_price = context.user_data.get("new_item_price")
        item_description = context.user_data.get("new_item_description")

        with models.session_scope() as s:
            new_item = models.Item(
                game_id=game_id,
                name=item_name,
                item_type=item_type,
                price=item_price,
                description=item_description,
                stock_quantity=None,
                is_active=True,
            )
            s.add(new_item)

        # Clean up user_data
        context.user_data.pop("new_item_game_id", None)
        context.user_data.pop("new_item_name", None)
        context.user_data.pop("new_item_type", None)
        context.user_data.pop("new_item_price", None)
        context.user_data.pop("new_item_description", None)

        await update.callback_query.answer(
            text=TEXTS[lang]["item_added_success"],
            show_alert=True,
        )
        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


async def get_item_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)

        item_stock = int(update.message.text.strip())
        game_id = context.user_data.get("new_item_game_id")
        item_name = context.user_data.get("new_item_name")
        item_type = context.user_data.get("new_item_type")
        item_price = context.user_data.get("new_item_price")
        item_description = context.user_data.get("new_item_description")

        with models.session_scope() as s:
            new_item = models.Item(
                game_id=game_id,
                name=item_name,
                item_type=item_type,
                price=item_price,
                description=item_description,
                stock_quantity=item_stock,
                is_active=True,
            )
            s.add(new_item)

        # Clean up user_data
        context.user_data.pop("new_item_game_id", None)
        context.user_data.pop("new_item_name", None)
        context.user_data.pop("new_item_type", None)
        context.user_data.pop("new_item_price", None)
        context.user_data.pop("new_item_description", None)

        await update.message.reply_text(
            text=TEXTS[lang]["item_added_success"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        return ConversationHandler.END


add_item_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_item,
            r"^add_item$",
        ),
    ],
    states={
        ITEM_GAME: [
            CallbackQueryHandler(
                get_item_game,
                r"^[0-9]+$",
            ),
        ],
        ITEM_NAME: [
            MessageHandler(
                callback=get_item_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        ITEM_TYPE: [
            CallbackQueryHandler(
                get_item_type,
                r"^select_item_type_",
            ),
        ],
        ITEM_PRICE: [
            MessageHandler(
                callback=get_item_price,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        ITEM_DESCRIPTION: [
            MessageHandler(
                callback=get_item_description,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(skip_item_description, r"^skip_item_description$"),
        ],
        ITEM_STOCK: [
            MessageHandler(
                callback=get_item_stock,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
            CallbackQueryHandler(skip_item_stock, r"^skip_item_stock$"),
        ],
    },
    fallbacks=[
        items_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_get_item_game, r"^back_to_get_item_game$"),
        CallbackQueryHandler(back_to_get_item_name, r"^back_to_get_item_name$"),
        CallbackQueryHandler(back_to_get_item_type, r"^back_to_get_item_type$"),
        CallbackQueryHandler(back_to_get_item_price, r"^back_to_get_item_price$"),
        CallbackQueryHandler(
            back_to_get_item_description, r"^back_to_get_item_description$"
        ),
    ],
)

CHOOSE_GAME_TO_REMOVE_ITEM, CHOOSE_ITEM_TO_REMOVE = range(2)


async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            games = s.query(models.Game).all()

            if not games:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_games"],
                    show_alert=True,
                )
                return ConversationHandler.END

            game_keyboard = build_keyboard(
                columns=1,
                texts=[game.name for game in games],
                buttons_data=[f"remove_item_game_{game.id}" for game in games],
            )
            game_keyboard.append(build_back_button("back_to_items_settings", lang=lang))
            game_keyboard.append(build_back_to_home_page_button(lang=lang)[0])

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_game_to_remove_item"],
                reply_markup=InlineKeyboardMarkup(game_keyboard),
            )
        return CHOOSE_GAME_TO_REMOVE_ITEM


async def choose_item_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            if update.callback_query.data.isnumeric():
                # Remove the selected item
                item_id = int(update.callback_query.data)
                item = s.get(models.Item, item_id)
                if item:
                    game_id = item.game_id
                    s.delete(item)
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["item_removed_success"],
                        show_alert=True,
                    )
                else:
                    game_id = context.user_data.get("removing_item_game_id")
            else:
                # Show items for selected game
                game_id = int(update.callback_query.data.replace("remove_item_game_", ""))
                context.user_data["removing_item_game_id"] = game_id

            items = s.query(models.Item).filter(models.Item.game_id == game_id).all()

            if not items:
                context.user_data.pop("removing_item_game_id", None)
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_items_for_game"],
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

            item_keyboard = build_keyboard(
                columns=1,
                texts=[item.name for item in items],
                buttons_data=[str(item.id) for item in items],
            )
            item_keyboard.append(
                build_back_button("back_to_choose_game_to_remove_item", lang=lang)
            )
            item_keyboard.append(build_back_to_home_page_button(lang=lang)[0])

            game = s.get(models.Game, game_id)
            game_name = game.name if game else "N/A"
            text = TEXTS[lang]["remove_item_instruction"].format(game_name=game_name)
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(item_keyboard),
            )
        return CHOOSE_ITEM_TO_REMOVE


back_to_choose_game_to_remove_item = remove_item


remove_item_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            remove_item,
            "^remove_item$",
        ),
    ],
    states={
        CHOOSE_GAME_TO_REMOVE_ITEM: [
            CallbackQueryHandler(
                choose_item_to_remove,
                r"^remove_item_game_\d+$",
            ),
        ],
        CHOOSE_ITEM_TO_REMOVE: [
            CallbackQueryHandler(
                choose_item_to_remove,
                r"^\d+$",
            ),
        ],
    },
    fallbacks=[
        items_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_choose_game_to_remove_item,
            r"^back_to_choose_game_to_remove_item$",
        ),
    ],
)


(
    CHOOSE_GAME_TO_EDIT_ITEM,
    CHOOSE_ITEM_TO_EDIT,
    EDITING_ITEM_NAME,
    EDITING_ITEM_TYPE,
    EDITING_ITEM_PRICE,
    EDITING_ITEM_DESCRIPTION,
    EDITING_ITEM_STOCK,
    EDITING_ITEM_STATUS,
) = range(8)


async def edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
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
                buttons_data=[f"edit_item_game_{game.id}" for game in games],
            )
            game_keyboard.append(build_back_button("back_to_items_settings", lang=lang))
            game_keyboard.append(build_back_to_home_page_button(lang=lang)[0])

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_game_to_edit_item"],
                reply_markup=InlineKeyboardMarkup(game_keyboard),
            )
        return CHOOSE_GAME_TO_EDIT_ITEM


async def show_items_for_game_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            game_id = int(update.callback_query.data.replace("edit_item_game_", ""))
            context.user_data["editing_item_game_id"] = game_id
        else:
            game_id = context.user_data.get("editing_item_game_id")

        with models.session_scope() as s:
            items = s.query(models.Item).filter(models.Item.game_id == game_id).all()

            if not items:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_items_for_game"], show_alert=True
                )
                return CHOOSE_GAME_TO_EDIT_ITEM

            item_keyboard = []
            for item in items:
                item_keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=item.name,
                            callback_data=str(item.id),
                        ),
                    ]
                )
            item_keyboard.append(
                build_back_button("back_to_choose_game_to_edit_item", lang=lang)
            )
            item_keyboard.append(build_back_to_home_page_button(lang=lang)[0])

            game = s.get(models.Game, game_id)
            game_name = game.name if game else "N/A"
            text = TEXTS[lang]["select_item_to_edit"].format(game_name=game_name)
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(item_keyboard),
            )
        return CHOOSE_ITEM_TO_EDIT


back_to_choose_game_to_edit_item = edit_item


async def show_item_edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith(
            "back"
        ) and not update.callback_query.data.startswith("toggle_item_status"):
            item_id = int(update.callback_query.data)
            context.user_data["editing_item_id"] = item_id
        else:
            item_id = context.user_data["editing_item_id"]

        keyboard = build_edit_item_keyboard(lang)
        keyboard.append(build_back_button("back_to_choose_item_to_edit", lang=lang))
        keyboard.append(build_back_to_home_page_button(lang=lang)[0])

        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            # Ensure game relationship is loaded
            _ = item.game.name
            
            text = item.stringify(lang)
            text += f"\n\n{TEXTS[lang]['select_what_to_edit']}"

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return EDITING_ITEM_STATUS


back_to_choose_item_to_edit = edit_item


async def handle_edit_item_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        action = update.callback_query.data
        item_id = context.user_data.get("editing_item_id")

        back_buttons = [
            build_back_button("back_to_handle_edit_item_action", lang=lang),
            build_back_to_home_page_button(lang=lang)[0],
        ]
        if action == "toggle_item_status":
            with models.session_scope() as s:
                item = s.get(models.Item, item_id)
                if item:
                    item.is_active = not item.is_active
                    s.commit()
                    await update.callback_query.answer(
                        text=TEXTS[lang]["item_status_updated"],
                        show_alert=True,
                    )
                    return await show_item_edit_options(update, context)
        elif action == "edit_item_name":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_item_name"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_ITEM_NAME
        elif action == "edit_item_type":
            type_keyboard = build_item_type_keyboard(
                lang, context.user_data.get("editing_item_type")
            )
            type_keyboard.append(
                build_back_button("back_to_handle_edit_item_action", lang=lang)
            )
            type_keyboard.append(build_back_to_home_page_button(lang=lang)[0])
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_new_item_type"],
                reply_markup=InlineKeyboardMarkup(type_keyboard),
            )
            return EDITING_ITEM_TYPE
        elif action == "edit_item_price":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_item_price"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_ITEM_PRICE
        elif action == "edit_item_description":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_item_description"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_ITEM_DESCRIPTION
        elif action == "edit_item_stock":
            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["enter_new_item_stock"],
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return EDITING_ITEM_STOCK


back_to_handle_edit_item_action = show_item_edit_options


async def save_item_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        item_id = context.user_data.get("editing_item_id")
        item_type_str = update.callback_query.data.replace("select_item_type_", "")
        item_type = models.ItemType(item_type_str)
        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            if item:
                item.item_type = item_type

        await update.callback_query.answer(
            text=TEXTS[lang]["item_type_updated"], show_alert=True
        )
        return await show_item_edit_options(update, context)


async def save_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        item_id = context.user_data.get("editing_item_id")
        new_name = update.message.text.strip()

        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            if item:
                item.name = new_name

        await update.message.reply_text(
            text=TEXTS[lang]["item_name_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_item_id", None)
        return ConversationHandler.END


async def save_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        item_id = context.user_data.get("editing_item_id")
        new_price = float(update.message.text.strip())
        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            if item:
                item.price = new_price

        await update.message.reply_text(
            text=TEXTS[lang]["item_price_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_item_id", None)
        return ConversationHandler.END


async def save_item_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        item_id = context.user_data.get("editing_item_id")
        new_description = update.message.text.strip() if update.message.text else None

        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            if item:
                item.description = new_description

        await update.message.reply_text(
            text=TEXTS[lang]["item_description_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_item_id", None)
        return ConversationHandler.END


async def save_item_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChatAndAdmin().filter(update) and PermissionFilter(
        models.Permission.MANAGE_ITEMS
    ).filter(update):
        lang = get_lang(update.effective_user.id)
        item_id = context.user_data.get("editing_item_id")
        item_stock = None
        item_stock = int(update.message.text.strip())
        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            if item:
                item.stock_quantity = item_stock

        await update.message.reply_text(
            text=TEXTS[lang]["item_stock_updated"],
        )
        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_admin_keyboard(lang, update.effective_user.id),
        )
        context.user_data.pop("editing_item_id", None)
        return ConversationHandler.END


edit_item_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            edit_item,
            r"^edit_item$",
        ),
    ],
    states={
        CHOOSE_GAME_TO_EDIT_ITEM: [
            CallbackQueryHandler(
                show_items_for_game_edit,
                r"^edit_item_game_",
            )
        ],
        CHOOSE_ITEM_TO_EDIT: [
            CallbackQueryHandler(
                show_item_edit_options,
                r"^[0-9]+$",
            ),
        ],
        EDITING_ITEM_STATUS: [
            CallbackQueryHandler(
                handle_edit_item_action,
                r"^edit_item_((name)|(type)|(price)|(description)|(stock))|toggle_item_status$",
            ),
        ],
        EDITING_ITEM_NAME: [
            MessageHandler(
                callback=save_item_name,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        EDITING_ITEM_TYPE: [
            CallbackQueryHandler(
                save_item_type,
                r"^select_item_type_",
            ),
        ],
        EDITING_ITEM_PRICE: [
            MessageHandler(
                callback=save_item_price,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        EDITING_ITEM_DESCRIPTION: [
            MessageHandler(
                callback=save_item_description,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
        EDITING_ITEM_STOCK: [
            MessageHandler(
                callback=save_item_stock,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
    },
    fallbacks=[
        items_settings_handler,
        admin_command,
        start_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_choose_game_to_edit_item,
            r"^back_to_choose_game_to_edit_item$",
        ),
        CallbackQueryHandler(
            back_to_choose_item_to_edit,
            r"^back_to_choose_item_to_edit$",
        ),
        CallbackQueryHandler(
            back_to_handle_edit_item_action,
            r"^back_to_handle_edit_item_action$",
        ),
    ],
)
