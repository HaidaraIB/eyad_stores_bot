from telegram.ext import Application, ContextTypes
from services.g2bulk_api import G2BulkAPI
import models
from common.lang_dicts import TEXTS, get_lang
from common.common import escape_html, format_float
import logging
from Config import Config

logger = logging.getLogger(__name__)


async def poll_api_orders_status(context: ContextTypes.DEFAULT_TYPE):
    """Poll API orders status and notify users when orders complete"""
    try:
        api = G2BulkAPI()

        # Get all non-terminal orders
        with models.session_scope() as s:
            non_terminal_orders = (
                s.query(models.ApiPurchaseOrder)
                .filter(
                    models.ApiPurchaseOrder.status.in_(
                        [
                            models.ApiPurchaseOrderStatus.PENDING,
                            models.ApiPurchaseOrderStatus.PROCESSING,
                        ]
                    )
                )
                .all()
            )

            if not non_terminal_orders:
                return

            logger.info(f"Polling {len(non_terminal_orders)} API orders...")

            for order in non_terminal_orders:
                try:
                    # Get order status from API
                    status_data = await api.get_order_status(
                        order.api_order_id, order.api_game.api_game_code
                    )

                    if not status_data.get("success"):
                        continue

                    order_info = status_data.get("order", {})
                    # Status might be in order object or root level
                    new_status_str = (
                        order_info.get("status") or status_data.get("status") or ""
                    ).lower()
                    api_message = (
                        status_data.get("message") or order_info.get("message") or ""
                    )
                    player_name = order_info.get("player_name")

                    # Map API status to our enum (handle both uppercase and lowercase)
                    status_mapping = {
                        "pending": models.ApiPurchaseOrderStatus.PENDING,
                        "processing": models.ApiPurchaseOrderStatus.PROCESSING,
                        "completed": models.ApiPurchaseOrderStatus.COMPLETED,
                        "failed": models.ApiPurchaseOrderStatus.FAILED,
                        "cancelled": models.ApiPurchaseOrderStatus.CANCELLED,
                        "canceled": models.ApiPurchaseOrderStatus.CANCELLED,  # Alternative spelling
                    }

                    new_status = status_mapping.get(new_status_str)
                    if not new_status:
                        continue

                    # Check if status changed
                    old_status = order.status
                    status_changed = old_status != new_status

                    # Update order in database
                    with models.session_scope() as update_session:
                        db_order = update_session.get(models.ApiPurchaseOrder, order.id)
                        if db_order:
                            db_order.status = new_status
                            if api_message:
                                db_order.api_message = api_message
                            if player_name:
                                db_order.player_name = player_name
                            update_session.commit()

                            # Notify user if status changed to terminal state
                            if status_changed and db_order.is_terminal():
                                await notify_user_order_status(
                                    context, db_order, old_status, new_status
                                )

                except Exception as e:
                    logger.error(
                        f"Error polling order {order.api_order_id}: {str(e)}",
                        exc_info=True,
                    )
                    continue

    except Exception as e:
        logger.error(f"Error in poll_api_orders_status: {str(e)}", exc_info=True)


async def notify_user_order_status(
    context: ContextTypes.DEFAULT_TYPE,
    order: models.ApiPurchaseOrder,
    old_status,
    new_status,
):
    """Notify user about order status change"""
    try:
        lang = get_lang(order.user_id)
        # Build notification message
        if new_status == models.ApiPurchaseOrderStatus.COMPLETED:
            status_emoji = "✅"
            status_text = TEXTS[lang].get(
                "api_order_completed",
                "Your order has been completed successfully!",
            )
        elif new_status == models.ApiPurchaseOrderStatus.FAILED:
            status_emoji = "❌"
            status_text = TEXTS[lang].get(
                "api_order_failed",
                "Your order has failed.",
            )
        elif new_status == models.ApiPurchaseOrderStatus.CANCELLED:
            status_emoji = "🚫"
            status_text = TEXTS[lang].get(
                "api_order_cancelled",
                "Your order has been cancelled.",
            )
        else:
            return  # Don't notify for non-terminal statuses

        message = f"{status_emoji} {status_text}\n\n"
        message += f"<b>{TEXTS[lang].get('order_id', 'Order ID')}:</b> <code>{order.api_order_id}</code>\n"
        message += f"<b>{TEXTS[lang].get('game', 'Game')}:</b> {escape_html(order.api_game.arabic_name if (lang == models.Language.ARABIC and order.api_game.arabic_name) else order.api_game.api_game_name)}\n"
        message += f"<b>{TEXTS[lang].get('denomination', 'Denomination')}:</b> {escape_html(order.denomination_name)}\n"
        message += f"<b>{TEXTS[lang].get('player_id', 'Player ID')}:</b> <code>{escape_html(order.player_id)}</code>\n"

        if order.player_name:
            message += f"<b>{TEXTS[lang].get('player_name', 'Player Name')}:</b> {escape_html(order.player_name)}\n"

        message += f"<b>{TEXTS[lang].get('price', 'Price')}:</b> <code>{format_float(order.price_sudan)} SDG</code>\n"

        # Send notification to user
        await context.bot.send_message(
            chat_id=order.user_id,
            text=message,
        )
        await context.bot.send_message(
            chat_id=Config.ARCHIVE_CHANNEL,
            text=message,
        )

        logger.info(
            f"Notified user {order.user_id} about order {order.api_order_id} status change: {old_status.value} -> {new_status.value}"
        )

    except Exception as e:
        logger.error(
            f"Error notifying user {order.user_id} about order {order.id}: {str(e)}",
            exc_info=True,
        )
