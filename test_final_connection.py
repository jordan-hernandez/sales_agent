#!/usr/bin/env python3
"""
Test Supabase connection - Windows compatible (no emojis)
"""
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env.example')

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password") 
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print(f"Connecting to Supabase:")
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
        sslmode='require'
    )
    print("SUCCESS: Connection established!")
    
    cursor = connection.cursor()
    
    # Test basic connection
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"SUCCESS: Current Time: {result[0]}")
    
    # Test PostgreSQL version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"SUCCESS: PostgreSQL: {version[:60]}...")
    
    # Test pgvector extension
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    vector_ext = cursor.fetchone()
    if vector_ext:
        print("SUCCESS: pgvector extension is available")
        
        # Test vector operations
        cursor.execute("SELECT '[1,2,3]'::vector;")
        test_vector = cursor.fetchone()[0]
        print(f"SUCCESS: Vector operations working: {test_vector}")
    else:
        print("WARNING: pgvector extension not found")
        print("Run this in Supabase SQL Editor: CREATE EXTENSION IF NOT EXISTS vector;")

    cursor.close()
    connection.close()
    print("SUCCESS: Connection closed properly")
    print("\n" + "="*50)
    print("SUPABASE CONNECTION IS WORKING!")
    print("="*50)
    print("Next step: Create database tables")

except Exception as e:
    print(f"ERROR: Connection failed: {e}")
    print("\nTroubleshooting steps:")
    print("1. Verify project is active in Supabase dashboard")
    print("2. Check that the connection string is exactly as shown in Settings > Database")
    print("3. Ensure the password is correct")