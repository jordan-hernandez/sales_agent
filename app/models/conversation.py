from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed" 
    ABANDONED = "abandoned"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    customer_phone = Column(String, index=True)
    customer_name = Column(String, nullable=True)
    platform = Column(String, default="telegram")  # telegram, whatsapp
    chat_id = Column(String, index=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    context = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    restaurant = relationship("Restaurant", back_populates="conversations")
    orders = relationship("Order", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")