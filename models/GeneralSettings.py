from datetime import datetime
import sqlalchemy as sa
from models.DB import Base


class GeneralSettings(Base):
    __tablename__ = "general_settings"
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    usd_to_sudan_rate = sa.Column(sa.Float, nullable=False, default=1.0)
    
    created_at = sa.Column(sa.DateTime, default=datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"GeneralSettings(usd_to_sudan_rate={self.usd_to_sudan_rate})"

