import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class OrderAdminMessage(Base):
    """Stores Telegram message IDs for order messages sent to each admin"""
    __tablename__ = "order_admin_messages"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    order_type = sa.Column(sa.String, nullable=False)  # "charging" or "purchase"
    order_id = sa.Column(sa.Integer, nullable=False)  # ID of the order
    admin_id = sa.Column(sa.BigInteger, nullable=False)  # Telegram user ID of the admin
    message_id = sa.Column(sa.Integer, nullable=False)  # Telegram message ID
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)

    def __repr__(self):
        return (
            f"OrderAdminMessage(id={self.id}, order_type={self.order_type}, "
            f"order_id={self.order_id}, admin_id={self.admin_id}, message_id={self.message_id})"
        )

