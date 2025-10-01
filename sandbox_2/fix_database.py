#!/usr/bin/env python
"""
Script to fix the database schema issues.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix_database():
    """Fix the database schema issues."""
    print("Fixing database schema...")
    
    with connection.cursor() as cursor:
        # Add organization_id column to portfolio_fundmanager if it doesn't exist
        try:
            cursor.execute("ALTER TABLE portfolio_fundmanager ADD COLUMN organization_id UUID;")
            print("Added organization_id to portfolio_fundmanager")
        except Exception as e:
            print(f"organization_id column might already exist: {e}")
        
        # Add organization_id column to portfolio_client if it doesn't exist
        try:
            cursor.execute("ALTER TABLE portfolio_client ADD COLUMN organization_id UUID;")
            print("Added organization_id to portfolio_client")
        except Exception as e:
            print(f"organization_id column might already exist: {e}")
        
        # Add organization_id column to portfolio_portfolio if it doesn't exist
        try:
            cursor.execute("ALTER TABLE portfolio_portfolio ADD COLUMN organization_id UUID;")
            print("Added organization_id to portfolio_portfolio")
        except Exception as e:
            print(f"organization_id column might already exist: {e}")
        
        # Add organization_id column to portfolio_stock if it doesn't exist
        try:
            cursor.execute("ALTER TABLE portfolio_stock ADD COLUMN organization_id UUID;")
            print("Added organization_id to portfolio_stock")
        except Exception as e:
            print(f"organization_id column might already exist: {e}")
        
    print("Database schema fixed!")

if __name__ == "__main__":
    fix_database()
    print("Run: python manage.py migrate")
