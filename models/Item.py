from enum import Enum
import sqlalchemy as sa
from sqlalchemy.orm import relationship
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
    stock_quantity = sa.Column(
        sa.Integer, nullable=True
    )  # Optional: for limited stock items

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    game = relationship("Game", back_populates="items")
    purchase_orders = relationship("PurchaseOrder", back_populates="item")

    def __repr__(self):
        return (
            f"Item(id={self.id}, game_id={self.game_id}, name={self.name}, "
            f"item_type={self.item_type.value}, price={self.price}, is_active={self.is_active})"
        )

    def stringify(self, lang):
        """Return a formatted HTML string preview of the item properties"""
        from common.lang_dicts import TEXTS, BUTTONS
        from common.common import escape_html, format_datetime, format_float

        texts = TEXTS[lang]
        lines = [
            f"<b>{escape_html(self.name)}</b>",
            "",
            f"<b>{texts.get('game', 'Game')}:</b> {escape_html(self.game.name)}",
            f"<b>{texts.get('type', 'Type')}:</b> <code>{BUTTONS[lang].get(f"item_type_{self.item_type.value}")}</code>",
            f"<b>{texts.get('price', 'Price')}:</b> <code>{format_float(self.price)}</code>",
            f"<b>{texts.get('status', 'Status')}:</b> {texts.get('active' if self.is_active else 'inactive', 'N/A')}",
        ]

        if self.description:
            lines.append(f"<b>{texts.get('description', 'Description')}:</b>")
            lines.append(f"<i>{escape_html(self.description)}</i>")

        if self.stock_quantity is not None:
            lines.append(
                f"<b>{texts.get('stock', 'Stock')}:</b> <code>{self.stock_quantity}</code>"
            )
        else:
            lines.append(
                f"<b>{texts.get('stock', 'Stock')}:</b> <i>{texts.get('unlimited', 'Unlimited')}</i>"
            )

        lines.extend(
            [
                "",
                f"<b>{texts.get('created', 'Created')}:</b> <code>{format_datetime(self.created_at)}</code>",
                f"<b>{texts.get('updated', 'Updated')}:</b> <code>{format_datetime(self.updated_at)}</code>",
            ]
        )

        return "\n".join(lines)
