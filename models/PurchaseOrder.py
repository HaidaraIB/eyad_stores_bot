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
            f"game_id={self.game_id}, item_id={self.item_id}, amount={self.amount}, status={self.status.value})"
        )
