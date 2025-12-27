from enum import Enum
import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class PaymentMethodType(Enum):
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    E_WALLET = "e_wallet"
    CRYPTO = "crypto"
    MOBILE_MONEY = "mobile_money"
    OTHER = "other"


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(
        sa.String, nullable=False
    )  # Display name (e.g., "Vodafone Cash", "Bank of Egypt")
    type = sa.Column(sa.Enum(PaymentMethodType), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    description = sa.Column(sa.Text, nullable=True)  # Description for users

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    addresses = relationship("PaymentMethodAddress", back_populates="payment_method")

    def __repr__(self):
        return f"PaymentMethod(id={self.id}, name={self.name}, type={self.type.value}, is_active={self.is_active})"

    def stringify(self, lang):
        """Return a formatted HTML string preview of the payment method properties"""
        from common.lang_dicts import TEXTS, BUTTONS
        from common.common import escape_html, format_datetime

        texts = TEXTS[lang]
        lines = [
            f"<b>{escape_html(self.name)}</b>",
            "",
            f"<b>{texts.get('type', 'Type')}:</b> <code>{BUTTONS[lang].get(f"payment_type_{self.type.value}")}</code>",
            f"<b>{texts.get('status', 'Status')}:</b> {texts.get('active' if self.is_active else 'inactive', 'N/A')}",
        ]

        if self.description:
            lines.append(f"<b>{texts.get('description', 'Description')}:</b>")
            lines.append(f"<i>{escape_html(self.description)}</i>")

        lines.extend(
            [
                "",
                f"<b>{texts.get('created', 'Created')}:</b> <code>{format_datetime(self.created_at)}</code>",
                f"<b>{texts.get('updated', 'Updated')}:</b> <code>{format_datetime(self.updated_at)}</code>",
            ]
        )

        return "\n".join(lines)


class PaymentMethodAddress(Base):
    __tablename__ = "payment_method_addresses"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    payment_method_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("payment_methods.id", ondelete="CASCADE"),
        nullable=False,
    )
    label = sa.Column(
        sa.String, nullable=True
    )  # Label for the address (e.g., "Main Account", "Backup")
    address = sa.Column(
        sa.String, nullable=False
    )  # The actual payment address/account number
    account_name = sa.Column(sa.String, nullable=True)  # Account holder name
    additional_info = sa.Column(sa.Text, nullable=True)  # Any additional information
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    priority = sa.Column(
        sa.Integer, default=0, nullable=False
    )  # For ordering addresses

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    payment_method = relationship("PaymentMethod", back_populates="addresses")
    charging_balance_orders = relationship(
        "ChargingBalanceOrder", back_populates="payment_method_address"
    )

    def __repr__(self):
        return (
            f"PaymentMethodAddress(id={self.id}, payment_method_id={self.payment_method_id}, "
            f"label={self.label}, address={self.address})"
        )

    def stringify(self, lang):
        """Return a formatted HTML string preview of the payment address properties"""
        from common.lang_dicts import TEXTS
        from common.common import escape_html, format_datetime

        texts = TEXTS[lang]
        lines = []

        if self.label:
            lines.append(f"<b>{escape_html(self.label)}</b>")
        else:
            address_label = texts.get("address", "Address")
            lines.append(f"<b>{address_label} #{self.id}</b>")

        lines.append("")
        lines.append(
            f"<b>{texts.get('address', 'Address')}:</b> <code>{escape_html(self.address)}</code>"
        )

        if self.account_name:
            lines.append(
                f"<b>{texts.get('account_name', 'Account Name')}:</b> {escape_html(self.account_name)}"
            )

        if self.additional_info:
            lines.append(f"<b>{texts.get('additional_info', 'Additional Info')}:</b>")
            lines.append(f"<i>{escape_html(self.additional_info)}</i>")

        lines.extend(
            [
                "",
                f"<b>{texts.get('status', 'Status')}:</b> {texts.get('active' if self.is_active else 'inactive', 'N/A')}",
                f"<b>{texts.get('priority', 'Priority')}:</b> <code>{self.priority}</code>",
                f"<b>{texts.get('created', 'Created')}:</b> <code>{format_datetime(self.created_at)}</code>",
            ]
        )

        return "\n".join(lines)
