from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base
from pgvector.sqlalchemy import Vector


class ProductEmbedding(Base):
    """Store embeddings for products to enable semantic search"""
    __tablename__ = "product_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    
    # Text content that was embedded
    content = Column(Text)  # Combined name + description + category
    
    # Vector embedding (1536 dimensions for OpenAI, 384 for sentence-transformers)
    embedding = Column(Vector(384))  # Using sentence-transformers default
    
    # Metadata for filtering
    embedding_model = Column(String, default="sentence-transformers/all-MiniLM-L6-v2")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", backref="embedding")
    restaurant = relationship("Restaurant")


class ConversationMemory(Base):
    """Store conversation memories and preferences with embeddings"""
    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    customer_phone = Column(String, index=True)
    
    # Memory content
    memory_type = Column(String)  # 'preference', 'order_history', 'complaint', 'compliment'
    content = Column(Text)
    summary = Column(Text)  # Human-readable summary
    
    # Vector embedding for semantic search
    embedding = Column(Vector(384))
    
    # Importance and recency
    importance_score = Column(Float, default=1.0)  # 0-1, how important this memory is
    access_count = Column(Integer, default=0)  # How often this memory was retrieved
    last_accessed = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation")
    restaurant = relationship("Restaurant")


class KnowledgeBase(Base):
    """Store FAQ and restaurant knowledge with embeddings"""
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    
    # Knowledge content
    question = Column(Text)
    answer = Column(Text)
    category = Column(String)  # 'faq', 'policy', 'menu_info', 'hours', 'delivery'
    tags = Column(ARRAY(String))  # Searchable tags
    
    # Combined content for embedding
    searchable_content = Column(Text)  # question + answer + tags
    embedding = Column(Vector(384))
    
    # Usage stats
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Admin fields
    active = Column(String, default=True)
    priority = Column(Integer, default=1)  # Higher = more important
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    restaurant = relationship("Restaurant")


class SearchLog(Base):
    """Log semantic searches for analytics and improvement"""
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    
    # Search details
    query = Column(Text)
    search_type = Column(String)  # 'products', 'knowledge', 'memory'
    embedding = Column(Vector(384))
    
    # Results
    results_found = Column(Integer)
    top_similarity = Column(Float)  # Highest similarity score
    results_used = Column(JSON)  # Which results were actually used
    
    # Performance
    search_time_ms = Column(Integer)
    embedding_time_ms = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation")
    restaurant = relationship("Restaurant")