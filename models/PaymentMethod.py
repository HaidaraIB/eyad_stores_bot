from enum import Enum
import sqlalchemy as sa
from models.DB import Base
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
    name = sa.Column(sa.String, nullable=False)  # Display name (e.g., "Vodafone Cash", "Bank of Egypt")
    type = sa.Column(sa.Enum(PaymentMethodType), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    description = sa.Column(sa.Text, nullable=True)  # Description for users
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"PaymentMethod(id={self.id}, name={self.name}, type={self.type.value}, is_active={self.is_active})"


class PaymentMethodAddress(Base):
    __tablename__ = "payment_method_addresses"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    payment_method_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("payment_methods.id", ondelete="CASCADE"),
        nullable=False,
    )
    label = sa.Column(sa.String, nullable=True)  # Label for the address (e.g., "Main Account", "Backup")
    address = sa.Column(sa.String, nullable=False)  # The actual payment address/account number
    account_name = sa.Column(sa.String, nullable=True)  # Account holder name
    bank_name = sa.Column(sa.String, nullable=True)  # Bank name (if applicable)
    branch = sa.Column(sa.String, nullable=True)  # Branch name (if applicable)
    additional_info = sa.Column(sa.Text, nullable=True)  # Any additional information
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    priority = sa.Column(sa.Integer, default=0, nullable=False)  # For ordering addresses
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return (
            f"PaymentMethodAddress(id={self.id}, payment_method_id={self.payment_method_id}, "
            f"label={self.label}, address={self.address})"
        )

