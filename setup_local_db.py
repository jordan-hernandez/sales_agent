#!/usr/bin/env python3
"""
Setup script for local PostgreSQL database as fallback
"""
import subprocess
import sys
import os

def check_postgresql():
    """Check if PostgreSQL is installed locally"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ PostgreSQL not found locally")
    return False

def create_local_database():
    """Create local database for development"""
    try:
        # Create database
        subprocess.run([
            'createdb', 'sales_agent_db'
        ], check=True)
        print("✅ Local database 'sales_agent_db' created")
        
        # Create user (optional)
        subprocess.run([
            'psql', '-d', 'sales_agent_db', '-c',
            "CREATE USER sales_user WITH PASSWORD 'sales_pass';"
        ], check=True)
        
        subprocess.run([
            'psql', '-d', 'sales_agent_db', '-c',
            "GRANT ALL PRIVILEGES ON DATABASE sales_agent_db TO sales_user;"
        ], check=True)
        
        print("✅ Database user created with permissions")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Setting up local PostgreSQL database...")
    
    if not check_postgresql():
        print("\n📥 To install PostgreSQL:")
        print("1. Download from: https://www.postgresql.org/download/windows/")
        print("2. Or use chocolatey: choco install postgresql")
        print("3. Or use winget: winget install PostgreSQL.PostgreSQL")
        sys.exit(1)
    
    if create_local_database():
        print("\n✅ Local database setup complete!")
        print("\n📝 Update your .env file with:")
        print("DATABASE_URL=postgresql://sales_user:sales_pass@localhost/sales_agent_db")
    else:
        print("❌ Database setup failed")