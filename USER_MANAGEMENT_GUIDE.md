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
# Enter password for user 'john_doe': [hidden input]
# Confirm password: [hidden input]
```

#### Delete a User
```bash
python manage_users.py delete <username>
```

**Example:**
```bash
python manage_users.py delete john_doe
# ⚠️  Are you sure you want to delete user 'john_doe'? (yes/no): yes
```

#### Reset a User's Password
```bash
python manage_users.py reset <username>
```

**Example:**
```bash
python manage_users.py reset john_doe
# Enter new password for user 'john_doe': [hidden input]
# Confirm password: [hidden input]
```

### Using the API Directly (Alternative Method)

You can also create users programmatically using the backend API:

```bash
curl -X POST http://localhost:8000/auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "securepass123"}'
```

## Security Best Practices

### Password Requirements
- **Minimum length**: 6 characters
- **Maximum length**: 72 characters (for bcrypt compatibility)
- **Recommendation**: Use strong, complex passwords with mix of letters, numbers, and special characters

### User Management Guidelines

1. **Create user accounts only for authorized personnel**
2. **Use strong, unique passwords for each user**
3. **Regularly review user list** - Remove access for users who no longer need it
4. **Reset passwords immediately** if a security breach is suspected
5. **Keep track of who has access** - Use the `list` command regularly

### Example Workflow

```bash
# 1. List current users
python manage_users.py list

# 2. Create a new authorized user
python manage_users.py create authorized_user

# 3. Verify the user was created
python manage_users.py list

# 4. If user forgets password, reset it
python manage_users.py reset authorized_user

# 5. If user no longer needs access, delete the account
python manage_users.py delete authorized_user
```

## Authentication Flow

1. **Login**: Users authenticate with username/password
2. **Token Issuance**: Backend issues a JWT token (valid for 20 minutes)
3. **Protected Access**: Users can access protected routes with valid token
4. **Auto-logout**: System automatically logs out when token expires

## Troubleshooting

### User cannot login
1. Verify user exists: `python manage_users.py list`
2. Reset password: `python manage_users.py reset <username>`
3. Check backend is running: `curl http://localhost:8000/auth/token`

### Forgot admin access
If you need to create a first user after clearing the database:
```bash
python manage_users.py create admin
```

### Password too long error
The system automatically handles passwords up to 72 characters. If you encounter issues, try a shorter password.

## Notes

- Users are stored in PostgreSQL database
- Passwords are hashed using bcrypt
- JWT tokens expire after 20 minutes
- No public registration endpoint is available for security
- All user management requires local/administrative access

