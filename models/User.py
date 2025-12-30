import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from models.Language import Language
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    user_id = sa.Column(sa.BigInteger, primary_key=True)
    username = sa.Column(sa.String)
    name = sa.Column(sa.String)
    lang = sa.Column(sa.Enum(Language), default=Language.ARABIC)
    is_banned = sa.Column(sa.Boolean, default=0)
    is_admin = sa.Column(sa.Boolean, default=0)
    balance = sa.Column(sa.Numeric(10, 2), default=0.00, nullable=False)

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    charging_balance_orders = relationship("ChargingBalanceOrder", back_populates="user")
    purchase_orders = relationship("PurchaseOrder", back_populates="user")
    api_purchase_orders = relationship("ApiPurchaseOrder", back_populates="user")
    

    def __str__(self):
        return (
            f"ID: <code>{self.user_id}</code>\n"
            f"Username: {f'@{self.username}' if self.username else 'N/A'}\n"
            f"Name: <b>{self.name}</b>"
        )

    def stringify(self, lang):
        """Return a formatted HTML string preview of the user properties"""
        from common.lang_dicts import TEXTS
        from common.common import escape_html

        texts = TEXTS[lang]
        username_text = f"@{self.username}" if self.username else texts.get("not_available", "N/A")
        
        lines = [
            f"<b>{texts.get('user_id', 'ID')}:</b> <code>{self.user_id}</code>",
            f"<b>{texts.get('username', 'Username')}:</b> {username_text}",
            f"<b>{texts.get('name', 'Name')}:</b> <b>{escape_html(self.name)}</b>",
        ]

        return "\n".join(lines)

    def __repr__(self):
        return f"User(user_id={self.user_id}, username={self.username}, name={self.name}, is_admin={bool(self.is_admin)}, is_banned={bool(self.is_banned)}"
