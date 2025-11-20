#!/usr/bin/env python3
"""
Simple script to create a user via the backend API
Usage: python create_user.py <username> <password>
"""

import requests
import sys

def create_user(username, password):
    """Create a new user via the backend API"""
    url = "http://localhost:8000/auth/"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 201:
            print(f"✅ User '{username}' created successfully!")
            return True
        elif response.status_code == 400:
            print(f"❌ Error: Username '{username}' already exists")
            return False
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        print("Example: python create_user.py admin mypassword123")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    print(f"Creating user: {username}")
    create_user(username, password)
