from enum import Enum
import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class ChargingOrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChargingBalanceOrder(Base):
    __tablename__ = "charging_balance_orders"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_method_address_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("payment_method_addresses.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    status = sa.Column(
        sa.Enum(ChargingOrderStatus),
        default=ChargingOrderStatus.PENDING,
        nullable=False,
    )
    payment_proof = sa.Column(
        sa.String, nullable=True
    )  # File ID or URL for payment proof
    admin_notes = sa.Column(sa.Text, nullable=True)  # Admin notes about the order
    assigned_admin_id = sa.Column(
        sa.BigInteger, nullable=True
    )  # ID of the admin currently handling this order

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="charging_balance_orders")
    payment_method_address = relationship(
        "PaymentMethodAddress", back_populates="charging_balance_orders"
    )

    def __repr__(self):
        return (
            f"ChargingBalanceOrder(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, status={self.status.value})"
        )

    def stringify(self, lang):
        """Return a formatted HTML string preview of the charging balance order properties"""
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
            f"<b>{texts['order_amount']}:</b> <code>{format_float(self.amount)}</code>",
            f"<b>{texts['order_date']}:</b> <code>{format_datetime(self.created_at)}</code>",
        ]

        if self.payment_method_address:
            pm = self.payment_method_address.payment_method
            lines.append(f"<b>{texts['payment_method']}:</b> {escape_html(pm.name)}")
            lines.append(f"<b>{texts['payment_address']}:</b> <code>{escape_html(self.payment_method_address.address)}</code>")

        if self.payment_proof:
            lines.append("")
            lines.append(f"<b>{texts['payment_proof']}:</b> ✅")

        if self.admin_notes:
            lines.append("")
            lines.append(f"<b>{texts.get('admin_notes', 'Admin Notes')}:</b>")
            lines.append(f"<i>{escape_html(self.admin_notes)}</i>")

        return "\n".join(lines)