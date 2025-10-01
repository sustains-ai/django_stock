#!/usr/bin/env python
"""
Script to fix the FundManager table schema.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix_fundmanager_schema():
    """Fix the FundManager table schema."""
    print("Fixing FundManager table schema...")
    
    with connection.cursor() as cursor:
        # Add missing columns to portfolio_fundmanager
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN license_number VARCHAR(100);")
            print("Added license_number to portfolio_fundmanager")
        except Exception as e:
            print(f"license_number column might already exist: {e}")
        
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN company_name VARCHAR(200);")
            print("Added company_name to portfolio_fundmanager")
        except Exception as e:
            print(f"company_name column might already exist: {e}")
        
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN phone VARCHAR(20);")
            print("Added phone to portfolio_fundmanager")
        except Exception as e:
            print(f"phone column might already exist: {e}")
        
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN is_active BOOLEAN DEFAULT TRUE;")
            print("Added is_active to portfolio_fundmanager")
        except Exception as e:
            print(f"is_active column might already exist: {e}")
        
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN created_at TIMESTAMP DEFAULT NOW();")
            print("Added created_at to portfolio_fundmanager")
        except Exception as e:
            print(f"created_at column might already exist: {e}")
        
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();")
            print("Added updated_at to portfolio_fundmanager")
        except Exception as e:
            print(f"updated_at column might already exist: {e}")
        
    print("FundManager table schema fixed!")

if __name__ == "__main__":
    fix_fundmanager_schema()
    print("FundManager schema fixed!")
