import sqlalchemy as sa
from models.DB import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class Game(Base):
    __tablename__ = "games"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, nullable=False)  # e.g., "PUBG Mobile", "Free Fire"
    code = sa.Column(
        sa.String, nullable=False, unique=True
    )  # e.g., "pubg", "free_fire" (for internal use)
    description = sa.Column(sa.Text, nullable=True)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)

    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship("Item", back_populates="game")

    def __str__(self):
        return f"{self.name} ({self.code})"

    def __repr__(self):
        return f"Game(id={self.id}, name={self.name}, code={self.code}, is_active={self.is_active})"

    def stringify(self, lang):
        """Return a formatted HTML string preview of the game properties"""
        from common.lang_dicts import TEXTS
        from common.common import escape_html, format_datetime
        import models
        
        texts = TEXTS[lang]
        lines = [
            f"<b>{escape_html(self.name)}</b>",
            f"<code>{escape_html(self.code)}</code>",
            "",
            f"<b>{texts.get('status', 'Status')}:</b> {texts.get('active' if self.is_active else 'inactive', 'N/A')}",
        ]
        
        if self.description:
            lines.append(f"<b>{texts.get('description', 'Description')}:</b>")
            lines.append(f"<i>{escape_html(self.description)}</i>")
        
        lines.extend([
            "",
            f"<b>{texts.get('created', 'Created')}:</b> <code>{format_datetime(self.created_at)}</code>",
            f"<b>{texts.get('updated', 'Updated')}:</b> <code>{format_datetime(self.updated_at)}</code>",
        ])
        
        return "\n".join(lines)
