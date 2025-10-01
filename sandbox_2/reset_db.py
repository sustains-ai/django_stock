#!/usr/bin/env python
"""
Script to reset the database and apply SaaS migrations.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def reset_database():
    """Reset the database by dropping and recreating tables."""
    print("Resetting database...")
    
    with connection.cursor() as cursor:
        # Drop all tables in the portfolio app
        tables = [
            'portfolio_stock',
            'portfolio_portfolio', 
            'portfolio_client',
            'portfolio_fundmanager',
            'portfolio_organizationadmin',
            'portfolio_organization',
            'portfolio_subscription',
            'portfolio_historicalstockdata',
            'portfolio_institute'
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        
        # Reset migration history
        cursor.execute("DELETE FROM django_migrations WHERE app = 'portfolio';")
        
    print("Database reset complete!")
    print("Now applying migrations...")

if __name__ == "__main__":
    reset_database()
    print("Run: python manage.py migrate")
