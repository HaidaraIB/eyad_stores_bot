from enum import Enum
import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class PurchaseOrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
    )
    game_account_id = sa.Column(
        sa.String, nullable=False
    )  # User's game account ID/username
    status = sa.Column(
        sa.Enum(PurchaseOrderStatus),
        default=PurchaseOrderStatus.PENDING,
        nullable=False,
    )
    admin_notes = sa.Column(sa.Text, nullable=True)  # Admin notes about the order

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="purchase_orders")
    item = relationship("Item", back_populates="purchase_orders")

    def __repr__(self):
        return (
            f"PurchaseOrder(id={self.id}, user_id={self.user_id}, "
            f"item_id={self.item_id}, status={self.status.value})"
        )

    def stringify(self, lang):
        """Return a formatted HTML string preview of the purchase order properties"""
        from common.lang_dicts import TEXTS
        from common.common import escape_html, format_datetime, format_float

        texts = TEXTS[lang]
        from common.common import get_status_emoji
        status_emoji = get_status_emoji(self.status)
        status_text = texts.get(f"order_status_{self.status.value}", self.status.value)
        
        lines = [
            f"<b>{texts['order_details_text']}</b>",
            "",
            f"<b>{texts['order_id']}:</b> <code>{self.id}</code>",
            f"<b>{texts['order_status']}:</b> {status_text} {status_emoji}",
            f"<b>{texts['order_date']}:</b> <code>{format_datetime(self.created_at)}</code>",
        ]

        if self.item:
            lines.append(f"<b>{texts['item_name']}:</b> {escape_html(self.item.name)}")
            lines.append(f"<b>{texts['game_name']}:</b> {escape_html(self.item.game.name)}")
            lines.append(f"<b>{texts.get('price', 'Price')}:</b> <code>{format_float(self.item.price)}</code>")

        lines.append(f"<b>{texts['game_account_id']}:</b> <code>{escape_html(self.game_account_id)}</code>")

        if self.admin_notes:
            lines.append("")
            lines.append(f"<b>{texts.get('admin_notes', 'Admin Notes')}:</b>")
            lines.append(f"<i>{escape_html(self.admin_notes)}</i>")

        return "\n".join(lines)
