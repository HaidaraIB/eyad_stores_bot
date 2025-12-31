from enum import Enum
import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class ApiPurchaseOrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApiPurchaseOrder(Base):
    __tablename__ = "api_purchase_orders"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    api_order_id = sa.Column(
        sa.Integer, nullable=False, unique=True
    )  # Order ID from G2Bulk API
    api_game_code = sa.Column(
        sa.String,
        sa.ForeignKey("api_games.api_game_code", ondelete="SET NULL"),
        nullable=False,
    )
    denomination_name = sa.Column(sa.String, nullable=False)  # Denomination name
    player_id = sa.Column(sa.String, nullable=False)  # Player ID
    player_name = sa.Column(sa.String, nullable=True)  # Player name (from API)
    server_id = sa.Column(sa.String, nullable=True)  # Server ID if required
    price_usd = sa.Column(sa.Numeric(10, 2), nullable=False)  # Price in USD
    price_sudan = sa.Column(
        sa.Numeric(10, 2), nullable=False
    )  # Price in Sudan currency
    status = sa.Column(
        sa.Enum(ApiPurchaseOrderStatus),
        default=ApiPurchaseOrderStatus.PENDING,
        nullable=False,
    )
    api_message = sa.Column(sa.Text, nullable=True)  # Message from API
    remark = sa.Column(sa.Text, nullable=True)  # Remark/notes

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="api_purchase_orders")
    api_game = relationship("ApiGame", back_populates="api_purchase_orders")

    def __repr__(self):
        return (
            f"ApiPurchaseOrder(id={self.id}, user_id={self.user_id}, "
            f"api_order_id={self.api_order_id}, status={self.status.value})"
        )

    def stringify(self, lang):
        """Return a formatted HTML string preview of the API purchase order properties"""
        from common.lang_dicts import TEXTS
        from common.common import escape_html, format_datetime, format_float

        texts = TEXTS[lang]
        from common.common import get_status_emoji
        status_emoji = get_status_emoji(self.status)
        status_text = texts.get(
            f"api_order_status_{self.status.value}", self.status.value
        )
        game_display_name = (
            self.api_game.get_display_name(lang) if self.api_game else "N/A"
        )

        lines = [
            f"<b>{texts.get('order_details_text', 'Order Details')}</b>",
            "",
            f"<b>{texts.get('order_id', 'Order ID')}:</b> <code>{self.id}</code>",
            f"<b>{texts.get('api_order_id', 'API Order ID')}:</b> <code>{self.api_order_id}</code>",
            f"<b>{texts.get('order_status', 'Status')}:</b> {status_text} {status_emoji}",
            f"<b>{texts.get('game', 'Game')}:</b> {escape_html(game_display_name)}",
            f"<b>{texts.get('denomination', 'Denomination')}:</b> {escape_html(self.denomination_name)}",
            f"<b>{texts.get('player_id', 'Player ID')}:</b> <code>{escape_html(self.player_id)}</code>",
        ]

        if self.player_name:
            lines.append(
                f"<b>{texts.get('player_name', 'Player Name')}:</b> {escape_html(self.player_name)}"
            )

        if self.server_id:
            lines.append(
                f"<b>{texts.get('server_id', 'Server ID')}:</b> <code>{escape_html(self.server_id)}</code>"
            )

        lines.extend(
            [
                f"<b>{texts.get('price', 'Price')}:</b> <code>{format_float(self.price_sudan)} SDG</code>",
                f"<b>{texts.get('order_date', 'Order Date')}:</b> <code>{format_datetime(self.created_at)}</code>",
            ]
        )

        if self.api_message:
            lines.append("")
            lines.append(f"<b>{texts.get('message', 'Message')}:</b>")
            lines.append(f"<i>{escape_html(self.api_message)}</i>")

        if self.remark:
            lines.append("")
            lines.append(f"<b>{texts.get('remark', 'Remark')}:</b>")
            lines.append(f"<i>{escape_html(self.remark)}</i>")

        return "\n".join(lines)

    def is_terminal(self) -> bool:
        """Check if order status is terminal (completed, failed, cancelled)"""
        return self.status in [
            ApiPurchaseOrderStatus.COMPLETED,
            ApiPurchaseOrderStatus.FAILED,
            ApiPurchaseOrderStatus.CANCELLED,
        ]
