from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from datetime import datetime
from .database import Base
import enum

class IPOStatus(enum.Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    LISTED = "listed"

class IPOMaster(Base):
    __tablename__ = "ipo_master"

    id = Column(Integer, primary_key=True, index=True)
    ipo_name = Column(String, index=True)
    gmp = Column(Float, nullable=True)
    retail_sub = Column(Float, nullable=True)
    hni_sub = Column(Float, nullable=True)
    qib_sub = Column(Float, nullable=True)
    issue_size = Column(Float, nullable=True)
    price_high = Column(Float, nullable=True)
    listing_gain = Column(Float, nullable=True)
    listing_date = Column(DateTime, nullable=True)
    best_category = Column(String, nullable=True) # Retail, HNI, QIB
    status = Column(String, default="upcoming") # stored as string for simplicity
    scraped_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IPO {self.ipo_name} (Status: {self.status})>"
