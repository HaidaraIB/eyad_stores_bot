from enum import Enum
import sqlalchemy as sa
from models.DB import Base
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
    payment_method_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("payment_methods.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    status = sa.Column(
        sa.Enum(ChargingOrderStatus),
        default=ChargingOrderStatus.PENDING,
        nullable=False,
    )
    payment_proof = sa.Column(sa.String, nullable=True)  # File ID or URL for payment proof
    admin_notes = sa.Column(sa.Text, nullable=True)  # Admin notes about the order
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return (
            f"ChargingBalanceOrder(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, status={self.status.value})"
        )

