#!/usr/bin/env python3
"""
Test Supabase connection using individual environment variables
"""
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv('.env.example')

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password") 
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print(f"Connecting with:")
print(f"  Host: {HOST}")
print(f"  User: {USER}")
print(f"  Database: {DBNAME}")
print(f"  Port: {PORT}")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        sslmode='require'  # Required for Supabase
    )
    print("✅ Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Test basic connection
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"✅ Current Time: {result[0]}")
    
    # Test PostgreSQL version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ PostgreSQL: {version[:50]}...")
    
    # Test pgvector extension
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    vector_ext = cursor.fetchone()
    if vector_ext:
        print("✅ pgvector extension is available")
        
        # Test vector operations
        cursor.execute("SELECT '[1,2,3]'::vector;")
        test_vector = cursor.fetchone()[0]
        print(f"✅ Vector operations working: {test_vector}")
    else:
        print("⚠️  pgvector extension not found")

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("✅ Connection closed successfully.")
    print("\n🎉 All tests passed! Supabase is ready!")

except psycopg2.OperationalError as e:
    print(f"❌ Connection failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("1. Verify your Supabase project is active at supabase.com")
    print("2. Check that the host URL is correct")
    print("3. Ensure the password doesn't need URL encoding")
    print("4. Try pausing and resuming your Supabase project")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")