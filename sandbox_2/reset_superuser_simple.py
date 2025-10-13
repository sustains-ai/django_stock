#!/usr/bin/env python
"""
Simple script to delete all superusers and create a new one.
Run this script from the project root directory.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction

def reset_superuser():
    """Delete all superusers and create a new one."""
    
    # Get existing superusers
    existing_superusers = User.objects.filter(is_superuser=True)
    
    if existing_superusers.exists():
        print(f"Found {existing_superusers.count()} existing superuser(s):")
        for user in existing_superusers:
            print(f"  - {user.username} ({user.email})")
        
        confirm = input("\nDelete all existing superusers? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("Operation cancelled.")
            return
    
    # Delete existing superusers
    with transaction.atomic():
        deleted_count = existing_superusers.count()
        existing_superusers.delete()
        print(f"Successfully deleted {deleted_count} existing superuser(s).")
    
    # Create new superuser
    print("\nCreating new superuser:")
    username = input("Username: ")
    email = input("Email: ")
    password = input("Password: ")
    
    if not all([username, email, password]):
        print("Error: All fields are required.")
        return
    
    try:
        with transaction.atomic():
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                print(f"Error: Username '{username}' already exists.")
                return
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                print(f"Error: Email '{email}' already exists.")
                return
            
            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            print(f"Successfully created new superuser: {username} ({email})")
            
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    reset_superuser()
