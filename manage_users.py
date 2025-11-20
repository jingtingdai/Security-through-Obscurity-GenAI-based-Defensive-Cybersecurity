#!/usr/bin/env python3
"""
User Management Script
This script allows administrators to manage authorized users.

Usage:
    python manage_users.py list                    # List all users
    python manage_users.py create <username>        # Create a new user
    python manage_users.py delete <username>        # Delete a user
    python manage_users.py reset <username>         # Reset user password
"""

import sys
import os
import requests
import getpass

sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'backend'))

from database import SessionLocal
from models import Users
from passlib.context import CryptContext

# Bcrypt context for password hashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def list_users():
    """List all users in the database"""
    db = SessionLocal()
    try:
        users = db.query(Users).all()
        if not users:
            print("No users found in database.")
            return
        
        print("\n" + "="*60)
        print(f"{'ID':<5} {'Username':<30} {'Created':<20}")
        print("="*60)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<30}")
        print("="*60)
        print(f"Total users: {len(users)}")
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()


def create_user(username):
    """Create a new user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(Users).filter(Users.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return False
        
        # Get password
        password = getpass.getpass(f"Enter password for user '{username}': ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long!")
            return False
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return False
        
        # Handle password length for bcrypt (72 byte limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        
        # Hash password and create user
        hashed_password = bcrypt_context.hash(password)
        
        new_user = Users(
            username=username,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        
        print(f"✅ User '{username}' created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def delete_user(username):
    """Delete a user"""
    db = SessionLocal()
    try:
        user = db.query(Users).filter(Users.username == username).first()
        
        if not user:
            print(f"❌ User '{username}' not found!")
            return False
        
        # Confirm deletion
        confirm = input(f"⚠️  Are you sure you want to delete user '{username}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled.")
            return False
        
        db.delete(user)
        db.commit()
        
        print(f"✅ User '{username}' deleted successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def reset_password(username):
    """Reset a user's password"""
    db = SessionLocal()
    try:
        user = db.query(Users).filter(Users.username == username).first()
        
        if not user:
            print(f"❌ User '{username}' not found!")
            return False
        
        # Get new password
        password = getpass.getpass(f"Enter new password for user '{username}': ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long!")
            return False
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return False
        
        # Handle password length for bcrypt (72 byte limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        
        # Hash password and update user
        user.hashed_password = bcrypt_context.hash(password)
        db.commit()
        
        print(f"✅ Password for user '{username}' reset successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main function to handle user management commands"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_users()
    
    elif command == 'create':
        if len(sys.argv) < 3:
            print("Usage: python manage_users.py create <username>")
            sys.exit(1)
        create_user(sys.argv[2])
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Usage: python manage_users.py delete <username>")
            sys.exit(1)
        delete_user(sys.argv[2])
    
    elif command == 'reset':
        if len(sys.argv) < 3:
            print("Usage: python manage_users.py reset <username>")
            sys.exit(1)
        reset_password(sys.argv[2])
    
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

