from telegram import (
    Update,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from user.user_calls.keyboards import (
    build_purchase_order_keyboard,
)
from common.keyboards import (
    build_user_keyboard,
    build_back_to_home_page_button,
    build_back_button,
    build_keyboard,
)
from common.lang_dicts import TEXTS, get_lang
from common.back_to_home_page import back_to_user_home_page_handler
from common.common import escape_html, format_float
from custom_filters import PrivateChat
from start import start_command
from Config import Config
import models

# Conversation states for purchase order
PURCHASE_ORDER_GAME, PURCHASE_ORDER_ITEM, PURCHASE_ORDER_ACCOUNT_ID = range(3)


async def purchase_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        with models.session_scope() as s:
            games = s.query(models.Game).filter(models.Game.is_active == True).all()

            if not games:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_active_games"],
                    show_alert=True,
                )
                return ConversationHandler.END

            game_keyboard = build_keyboard(
                columns=1,
                texts=[game.name for game in games],
                buttons_data=[str(game.id) for game in games],
            )
            game_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_game"],
                reply_markup=InlineKeyboardMarkup(game_keyboard),
            )
        return PURCHASE_ORDER_GAME


async def get_purchase_order_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            game_id = int(update.callback_query.data)
            context.user_data["purchase_order_game_id"] = game_id

        with models.session_scope() as s:
            game_id = context.user_data.get("purchase_order_game_id")
            items = (
                s.query(models.Item)
                .filter(models.Item.game_id == game_id, models.Item.is_active == True)
                .all()
            )

            if not items:
                await update.callback_query.answer(
                    text=TEXTS[lang]["no_items_for_game"],
                    show_alert=True,
                )
                return PURCHASE_ORDER_GAME

            item_keyboard = build_keyboard(
                columns=1,
                texts=[item.name for item in items],
                buttons_data=[str(item.id) for item in items],
            )
            item_keyboard.append(
                build_back_button("back_to_purchase_order_game", lang=lang)
            )
            item_keyboard.append(
                build_back_to_home_page_button(lang=lang, is_admin=False)[0]
            )

            await update.callback_query.edit_message_text(
                text=TEXTS[lang]["select_item"],
                reply_markup=InlineKeyboardMarkup(item_keyboard),
            )
        return PURCHASE_ORDER_ITEM


back_to_purchase_order_game = purchase_order


async def get_purchase_order_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        if not update.callback_query.data.startswith("back"):
            item_id = int(update.callback_query.data)
            context.user_data["purchase_order_item_id"] = item_id
        else:
            item_id = context.user_data["purchase_order_item_id"]

        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            user = s.get(models.User, update.effective_user.id)

            if not item or not item.is_active:
                await update.callback_query.answer(
                    text=TEXTS[lang]["item_not_found"],
                    show_alert=True,
                )
                return

            # Check if user has enough balance
            if user.balance < item.price:
                from common.common import format_float

                await update.callback_query.answer(
                    text=TEXTS[lang]["insufficient_balance"].format(
                        balance=format_float(user.balance),
                        price=format_float(item.price),
                    ),
                    show_alert=True,
                )
                return

        back_buttons = [
            build_back_button("back_to_purchase_order_item", lang=lang),
            build_back_to_home_page_button(lang=lang, is_admin=False)[0],
        ]

        await update.callback_query.edit_message_text(
            text=TEXTS[lang]["enter_game_account_id"],
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return PURCHASE_ORDER_ACCOUNT_ID


back_to_purchase_order_item = get_purchase_order_game


async def get_purchase_order_account_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if PrivateChat().filter(update):
        lang = get_lang(update.effective_user.id)
        game_account_id = update.message.text.strip()
        item_id = context.user_data.get("purchase_order_item_id")

        with models.session_scope() as s:
            item = s.get(models.Item, item_id)
            user = s.get(models.User, update.effective_user.id)

            # Create purchase order
            new_order = models.PurchaseOrder(
                user_id=update.effective_user.id,
                item_id=item_id,
                game_account_id=game_account_id,
                status=models.PurchaseOrderStatus.PENDING,
            )
            s.add(new_order)
            s.flush()  # To get the order ID
            order_id = new_order.id

            # Deduct balance
            user.balance -= item.price

            await update.message.reply_text(
                text=TEXTS[lang]["purchase_order_submitted"].format(
                    order_id=order_id
                ),
            )

            # Notify all admins with MANAGE_ORDERS permission
            try:
                notification_text = f"🔔 <b>New Purchase Order</b>\n\n"
                notification_text += f"Order ID: <code>{order_id}</code>\n"
                notification_text += f"User: {update.effective_user.mention_html()}\n"
                notification_text += f"Item: {escape_html(item.name)}\n"
                notification_text += f"Game: {escape_html(item.game.name)}\n"
                notification_text += f"Price: <code>{format_float(item.price)}</code>\n"
                notification_text += f"Game Account ID: <code>{escape_html(game_account_id)}</code>\n"
                notification_text += f"Status: {TEXTS[models.Language.ENGLISH]['order_status_pending']}"
                
                # Get all admins with MANAGE_ORDERS permission (including owner)
                with models.session_scope() as s:
                    # Get owner
                    admin_ids = [Config.OWNER_ID]
                    
                    # Get all admins with MANAGE_ORDERS permission
                    permissions = s.query(models.AdminPermission).filter(
                        models.AdminPermission.permission == models.Permission.MANAGE_ORDERS
                    ).all()
                    
                    for perm in permissions:
                        if perm.admin_id not in admin_ids:
                            admin_ids.append(perm.admin_id)
                
                # Send notification to all admins
                for admin_id in admin_ids:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=notification_text,
                            parse_mode="HTML",
                        )
                    except:
                        continue
            except:
                pass

        # Clean up user_data
        context.user_data.pop("purchase_order_game_id", None)
        context.user_data.pop("purchase_order_item_id", None)

        await update.message.reply_text(
            text=TEXTS[lang]["home_page"],
            reply_markup=build_user_keyboard(lang),
        )
        return ConversationHandler.END


purchase_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            purchase_order,
            r"^purchase_order$",
        ),
    ],
    states={
        PURCHASE_ORDER_GAME: [
            CallbackQueryHandler(
                get_purchase_order_game,
                r"^[0-9]+$",
            ),
        ],
        PURCHASE_ORDER_ITEM: [
            CallbackQueryHandler(
                get_purchase_order_item,
                r"^[0-9]+$",
            ),
        ],
        PURCHASE_ORDER_ACCOUNT_ID: [
            MessageHandler(
                callback=get_purchase_order_account_id,
                filters=filters.TEXT & ~filters.COMMAND,
            ),
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(
            back_to_purchase_order_game, r"^back_to_purchase_order_game$"
        ),
        CallbackQueryHandler(
            back_to_purchase_order_item, r"^back_to_purchase_order_item$"
        ),
    ],
)
