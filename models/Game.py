import sqlalchemy as sa
from models.DB import Base
from datetime import datetime


class Game(Base):
    __tablename__ = "games"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, nullable=False)  # e.g., "PUBG Mobile", "Free Fire"
    code = sa.Column(sa.String, nullable=False, unique=True)  # e.g., "pubg", "free_fire" (for internal use)
    description = sa.Column(sa.Text, nullable=True)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"Game(id={self.id}, name={self.name}, code={self.code}, is_active={self.is_active})"

