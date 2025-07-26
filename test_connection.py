#!/usr/bin/env python3
"""
Test Supabase connection with detailed error reporting
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.example')

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"Testing connection to: {DATABASE_URL}")

try:
    # Test connection
    print("Attempting to connect...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Test basic query
    print("✅ Connection successful!")
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ PostgreSQL version: {version[:50]}...")
    
    # Test pgvector
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    vector_ext = cursor.fetchone()
    if vector_ext:
        print("✅ pgvector extension is available")
    else:
        print("⚠️  pgvector extension not found")
    
    # Test vector operations
    cursor.execute("SELECT '[1,2,3]'::vector;")
    test_vector = cursor.fetchone()[0]
    print(f"✅ Vector operations working: {test_vector}")
    
    conn.close()
    print("\n🎉 All tests passed! Supabase connection is working correctly.")
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection Error: {e}")
    print("\n🔧 Possible solutions:")
    print("1. Verify your Supabase project is active")
    print("2. Check if the project URL is correct")
    print("3. Verify the password contains no special URL characters")
    print("4. Try accessing Supabase dashboard to confirm project status")
    
except Exception as e:
    print(f"❌ Unexpected Error: {e}")