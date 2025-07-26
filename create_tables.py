#!/usr/bin/env python3
"""
Create all database tables directly using SQLAlchemy
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all models to ensure they are registered
from app.models.restaurant import Restaurant
from app.models.product import Product  
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order, OrderItem
from app.models.embeddings import ProductEmbedding, ConversationMemory, KnowledgeBase, SearchLog
from app.core.database import Base, engine

def create_all_tables():
    """Create all tables in the database"""
    try:
        print("Creating all database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("SUCCESS: All tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
        print(f"\nTotal tables created: {len(Base.metadata.tables)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        return False

if __name__ == "__main__":
    success = create_all_tables()
    
    if success:
        print("\n" + "="*50)
        print("DATABASE SETUP COMPLETE!")
        print("="*50)
        print("Next steps:")
        print("1. Run setup script to create demo data")
        print("2. Start the FastAPI server")
        print("3. Test the Telegram bot")
    else:
        print("\nDatabase setup failed. Check the error above.")