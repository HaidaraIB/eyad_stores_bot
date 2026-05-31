from telegram.ext import ContextTypes
from services.provider_factory import get_provider
import models
from common.lang_dicts import TEXTS
from common.common import escape_html, format_float
import logging
from Config import Config

logger = logging.getLogger(__name__)


def schedule_immediate_order_poll(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll soon after purchase so the completion message arrives within seconds."""
    if not context.application.job_queue:
        return
    for delay in (3, 8, 15):
        context.application.job_queue.run_once(
            poll_api_orders_status,
            when=delay,
            name=f"poll_api_orders_once_{delay}s",
        )


async def poll_api_orders_status(context: ContextTypes.DEFAULT_TYPE):
    """Poll API orders status and notify users when orders complete"""
    try:
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
            order_ids = [order.id for order in non_terminal_orders]

        if not order_ids:
            return

        logger.info(f"Polling {len(order_ids)} API orders...")

        for order_id in order_ids:
            try:
                with models.session_scope() as s:
                    order = s.get(models.ApiPurchaseOrder, order_id)
                    if not order:
                        continue
                    provider = get_provider(order.api_provider)
                    game_code = order.api_game_code
                    api_order_id = order.api_order_id
                    old_status = order.status

                status_result = await provider.get_order_status(
                    str(api_order_id), game_code
                )

                new_status = status_result.status
                api_message = status_result.message or ""
                player_name = status_result.player_name
                voucher_codes = status_result.voucher_codes
                status_changed = old_status != new_status

                with models.session_scope() as update_session:
                    db_order = update_session.get(
                        models.ApiPurchaseOrder, order_id
                    )
                    if not db_order:
                        continue
                    db_order.status = new_status
                    if api_message:
                        db_order.api_message = api_message
                    if player_name:
                        db_order.player_name = player_name
                    if voucher_codes:
                        db_order.set_voucher_codes(voucher_codes)

                    if status_changed and new_status in [
                        models.ApiPurchaseOrderStatus.FAILED,
                        models.ApiPurchaseOrderStatus.CANCELLED,
                    ]:
                        user = update_session.get(
                            models.User, db_order.user_id
                        )
                        if user:
                            user.balance += db_order.price_sudan
                            logger.info(
                                f"Refunded {db_order.price_sudan} SDG to user {user.user_id} "
                                f"for failed/cancelled order {db_order.api_order_id}"
                            )

                if status_changed and new_status in [
                    models.ApiPurchaseOrderStatus.COMPLETED,
                    models.ApiPurchaseOrderStatus.FAILED,
                    models.ApiPurchaseOrderStatus.CANCELLED,
                ]:
                    await notify_user_order_status(
                        context,
                        order_id,
                        old_status,
                        new_status,
                    )

            except Exception as e:
                logger.error(
                    f"Error polling order id={order_id}: {str(e)}",
                    exc_info=True,
                )
                continue

    except Exception as e:
        logger.error(f"Error in poll_api_orders_status: {str(e)}", exc_info=True)


async def notify_user_order_status(
    context: ContextTypes.DEFAULT_TYPE,
    order_id: int,
    old_status,
    new_status,
):
    """Second message after purchase: completed, failed, or cancelled."""
    try:
        message = None
        user_id = None
        api_order_id = None
        user = None
        lang = models.Language.ARABIC

        with models.session_scope() as s:
            order = s.get(models.ApiPurchaseOrder, order_id)
            if not order:
                return
            user = s.get(models.User, order.user_id)
            lang = user.lang if user else models.Language.ARABIC

            if new_status == models.ApiPurchaseOrderStatus.COMPLETED:
                status_emoji = "✅"
                status_text = TEXTS[lang].get(
                    "api_order_completed",
                    "✅ Order completed successfully!",
                )
            elif new_status == models.ApiPurchaseOrderStatus.FAILED:
                status_emoji = "❌"
                status_text = TEXTS[lang].get(
                    "api_order_failed",
                    "Your order has failed.",
                )
                refund_text = TEXTS[lang].get(
                    "balance_refunded",
                    "Your balance has been refunded: {amount} SDG",
                ).format(amount=format_float(order.price_sudan))
                status_text += f"\n\n💰 {refund_text}"
            elif new_status == models.ApiPurchaseOrderStatus.CANCELLED:
                status_emoji = "🚫"
                status_text = TEXTS[lang].get(
                    "api_order_cancelled",
                    "Your order has been cancelled.",
                )
                refund_text = TEXTS[lang].get(
                    "balance_refunded",
                    "Your balance has been refunded: {amount} SDG",
                ).format(amount=format_float(order.price_sudan))
                status_text += f"\n\n💰 {refund_text}"
            else:
                return

            message = f"{status_emoji} {status_text}\n\n"
            message += (
                f"<b>{TEXTS[lang].get('order_id', 'Order ID')}:</b> "
                f"<code>{escape_html(str(order.api_order_id))}</code>\n"
            )
            api_game = (
                s.query(models.ApiGame)
                .filter(
                    models.ApiGame.api_game_code == order.api_game_code,
                    models.ApiGame.provider == order.api_provider,
                )
                .first()
            )
            game_name = "N/A"
            if api_game:
                game_name = (
                    api_game.arabic_name
                    if (lang == models.Language.ARABIC and api_game.arabic_name)
                    else api_game.api_game_name
                )
            message += (
                f"<b>{TEXTS[lang].get('game', 'Game')}:</b> {escape_html(game_name)}\n"
            )
            message += (
                f"<b>{TEXTS[lang].get('denomination', 'Denomination')}:</b> "
                f"{escape_html(order.denomination_name)}\n"
            )
            if order.player_id:
                message += (
                    f"<b>{TEXTS[lang].get('player_id', 'Player ID')}:</b> "
                    f"<code>{escape_html(order.player_id)}</code>\n"
                )
            if order.player_name:
                message += (
                    f"<b>{TEXTS[lang].get('player_name', 'Player Name')}:</b> "
                    f"{escape_html(order.player_name)}\n"
                )

            codes = order.get_voucher_codes()
            if codes:
                message += (
                    f"\n<b>{TEXTS[lang].get('voucher_codes', 'Voucher Codes')}:</b>\n"
                )
                for code in codes:
                    message += f"<code>{escape_html(code)}</code>\n"

            message += (
                f"<b>{TEXTS[lang].get('price', 'Price')}:</b> "
                f"<code>{format_float(order.price_sudan)} SDG</code>\n"
            )
            if order.api_message:
                message += (
                    f"\n<b>{TEXTS[lang].get('message', 'Message')}:</b> "
                    f"<i>{escape_html(order.api_message)}</i>"
                )

            user_id = order.user_id
            api_order_id = order.api_order_id

        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        if user:
            await context.bot.send_message(
                chat_id=Config.API_PURCHASES_ARCHIVE_CHANNEL,
                text=(
                    message
                    + "\n\n"
                    + f"<i>{TEXTS[lang].get('order_user_info', 'Order user info')}:</i>\n\n"
                    + user.stringify(lang)
                ),
                parse_mode="HTML",
            )

        logger.info(
            "Notified user %s about order %s status: %s -> %s",
            user_id,
            api_order_id,
            old_status.value,
            new_status.value,
        )

    except Exception as e:
        logger.error(
            "Error notifying about api order id=%s: %s",
            order_id,
            e,
            exc_info=True,
        )
