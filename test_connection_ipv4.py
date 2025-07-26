#!/usr/bin/env python3
"""
Test Supabase connection forcing IPv4
"""
import psycopg2
from dotenv import load_dotenv
import os
import socket

# Load environment variables
load_dotenv('.env.example')

# Force IPv4 resolution
def get_ipv4_address(hostname):
    try:
        return socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
    except:
        return hostname

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password") 
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print(f"Original host: {HOST}")

# Try to get IPv4 address
ipv4_host = get_ipv4_address(HOST)
print(f"Trying IPv4 address: {ipv4_host}")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=ipv4_host,  # Use IPv4 address
        port=PORT,
        dbname=DBNAME,
        sslmode='require',
        connect_timeout=10
    )
    print("✅ Connection successful!")
    
    cursor = connection.cursor()
    
    # Test basic queries
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"✅ Current Time: {result[0]}")
    
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ PostgreSQL: {version[:50]}...")
    
    # Test pgvector
    try:
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        vector_ext = cursor.fetchone()
        if vector_ext:
            print("✅ pgvector extension available")
            cursor.execute("SELECT '[1,2,3]'::vector;")
            test_vector = cursor.fetchone()[0]
            print(f"✅ Vector test: {test_vector}")
        else:
            print("⚠️ pgvector extension not found")
    except Exception as e:
        print(f"⚠️ pgvector test failed: {e}")

    cursor.close()
    connection.close()
    print("✅ Connection closed successfully")
    print("\n🎉 Supabase connection is working!")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    
    # Try alternative approaches
    print("\n🔧 Trying alternative connection methods...")
    
    # Method 2: Using DATABASE_URL
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            print(f"Trying DATABASE_URL: {db_url[:50]}...")
            connection = psycopg2.connect(db_url)
            print("✅ DATABASE_URL connection successful!")
            connection.close()
    except Exception as e2:
        print(f"❌ DATABASE_URL also failed: {e2}")
    
    print("\n📋 Next steps:")
    print("1. Verify project is active in Supabase dashboard")
    print("2. Check Settings → Database for correct connection string")
    print("3. Try pausing and resuming the project")
    print("4. Consider using session pooling mode")