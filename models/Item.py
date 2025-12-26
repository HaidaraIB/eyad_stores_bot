from enum import Enum
import sqlalchemy as sa
from models.DB import Base
from datetime import datetime


class ItemType(Enum):
    GAME_ACCOUNT = "game_account"
    GAME_ITEM = "game_item"
    GAME_PACKAGE = "game_package"
    GAME_BOOST = "game_boost"
    OTHER = "other"


class Item(Base):
    __tablename__ = "items"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    game_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = sa.Column(sa.String, nullable=False)  # Name of the item/package
    description = sa.Column(sa.Text, nullable=True)  # Description of the item
    item_type = sa.Column(sa.Enum(ItemType), nullable=False)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)  # Price of the item
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    stock_quantity = sa.Column(sa.Integer, nullable=True)  # Optional: for limited stock items
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return (
            f"Item(id={self.id}, game_id={self.game_id}, name={self.name}, "
            f"item_type={self.item_type.value}, price={self.price}, is_active={self.is_active})"
        )

