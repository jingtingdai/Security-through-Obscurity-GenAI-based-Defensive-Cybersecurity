# User Management Guide

## Overview
This system uses a closed authentication model where only authorized administrators can create and manage users. No public registration is available.

## Managing Authorized Users

### Using the Management Script

The `manage_users.py` script provides a secure way to manage users via command line.

#### List All Users
```bash
python manage_users.py list
```

#### Create a New User
```bash
python manage_users.py create <username>
```
The script will prompt you to enter a password securely (input is hidden).

**Example:**
```bash
python manage_users.py create john_doe
```

#### Delete a User
```bash
python manage_users.py delete <username>
```

**Example:**
```bash
python manage_users.py delete john_doe
```

#### Reset a User's Password
```bash
python manage_users.py reset <username>
```

**Example:**
```bash
python manage_users.py reset john_doe
```


## Authentication Flow

1. **Login**: Users authenticate with username/password
2. **Token Issuance**: Backend issues a JWT token (valid for 20 minutes)
3. **Protected Access**: Users can access protected routes with valid token
4. **Auto-logout**: System automatically logs out when token expires


## Notes

- Users are stored in PostgreSQL database
- Passwords are hashed using bcrypt
- JWT tokens expire after 20 minutes
- No public registration endpoint is available for security
- All user management requires local/administrative access

