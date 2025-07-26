#!/usr/bin/env python3
"""
Create basic database tables without vector types first
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.models.restaurant import Restaurant
from app.models.product import Product  
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order, OrderItem
from app.core.database import Base, engine

def create_basic_tables():
    """Create basic tables without vector dependencies"""
    try:
        print("Creating basic database tables...")
        
        # Only create basic tables first
        tables_to_create = [
            Restaurant.__table__,
            Product.__table__,
            Conversation.__table__, 
            Message.__table__,
            Order.__table__,
            OrderItem.__table__
        ]
        
        for table in tables_to_create:
            print(f"Creating table: {table.name}")
            table.create(bind=engine, checkfirst=True)
        
        print("SUCCESS: Basic tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table in tables_to_create:
            print(f"  - {table.name}")
            
        print(f"\nTotal basic tables created: {len(tables_to_create)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create basic tables: {e}")
        return False

if __name__ == "__main__":
    success = create_basic_tables()
    
    if success:
        print("\n" + "="*50)
        print("BASIC DATABASE SETUP COMPLETE!")
        print("="*50)
        print("Next steps:")
        print("1. Enable pgvector in Supabase: CREATE EXTENSION IF NOT EXISTS vector;")
        print("2. Create vector tables")
        print("3. Run setup script to create demo data")
    else:
        print("\nBasic database setup failed. Check the error above.")