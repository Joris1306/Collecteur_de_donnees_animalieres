#!/usr/bin/env python3
"""
User Management Script
Manage users (add, remove, change password, block/unblock)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from auth import add_user, load_users, save_users, verify_password, change_password, block_user, unblock_user, is_user_blocked


def list_users():
    """List all users"""
    users = load_users()
    if not users:
        print("No users found.")
        return
    print("\nRegistered users:")
    print("-" * 30)
    for username in users.keys():
        print(f"  - {username}")
    print()


def add_new_user():
    """Add a new user interactively"""
    print("\n=== Add New User ===")
    username = input("Username: ").strip()
    
    if not username:
        print("Username cannot be empty!")
        return
    
    password = input("Password: ").strip()
    if not password:
        print("Password cannot be empty!")
        return
    
    confirm = input("Confirm Password: ").strip()
    if password != confirm:
        print("Passwords do not match!")
        return
    
    if add_user(username, password):
        print(f"User '{username}' created successfully!")
    else:
        print(f"User '{username}' already exists!")


def remove_user():
    """Remove a user"""
    print("\n=== Remove User ===")
    list_users()
    username = input("Username to remove: ").strip()
    
    users = load_users()
    if username in users:
        confirm = input(f"Are you sure you want to remove '{username}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            del users[username]
            save_users(users)
            print(f"User '{username}' removed successfully!")
        else:
            print("Cancelled.")
    else:
        print(f"User '{username}' not found!")


def change_user_password():
    """Change user password"""
    print("\n=== Change Password ===")
    username = input("Username: ").strip()
    
    users = load_users()
    if username not in users:
        print(f"User '{username}' not found!")
        return
    
    old_password = input("Old Password: ").strip()
    
    if not verify_password(username, old_password):
        print("Old password is incorrect!")
        return
    
    new_password = input("New Password: ").strip()
    if not new_password:
        print("Password cannot be empty!")
        return
    
    confirm = input("Confirm New Password: ").strip()
    if new_password != confirm:
        print("Passwords do not match!")
        return
    
    if change_password(username, old_password, new_password):
        print(f"Password changed successfully for user '{username}'!")
    else:
        print("Failed to change password!")


def block_user_interactive():
    """Block a user (force logout)"""
    print("\n=== Block User ===")
    list_users()
    username = input("Username to block: ").strip()
    
    users = load_users()
    if username not in users:
        print(f"User '{username}' not found!")
        return
    
    if username == 'admin':
        confirm = input("Are you sure you want to block 'admin'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
    
    if block_user(username):
        print(f"User '{username}' has been blocked!")
        print(f"They will be logged out on next page access.")
    else:
        print(f"Failed to block user '{username}'!")


def unblock_user_interactive():
    """Unblock a user"""
    print("\n=== Unblock User ===")
    
    users = load_users()
    blocked_users = [u for u, d in users.items() if d.get('blocked', False)]
    
    if not blocked_users:
        print("No blocked users found.")
        return
    
    print("Blocked users:")
    for u in blocked_users:
        print(f"  - {u}")
    
    username = input("\nUsername to unblock: ").strip()
    
    if username not in users:
        print(f"User '{username}' not found!")
        return
    
    if unblock_user(username):
        print(f"User '{username}' has been unblocked!")
    else:
        print(f"Failed to unblock user '{username}'!")


def show_user_status():
    """Show user status (blocked/active)"""
    print("\n=== User Status ===")
    users = load_users()
    
    if not users:
        print("No users found.")
        return
    
    print(f"{'Username':<20} | {'Status':<10}")
    print("-" * 35)
    for username in users.keys():
        status = "BLOCKED" if is_user_blocked(username) else "ACTIVE"
        print(f"{username:<20} | {status:<10}")
    print()


def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 40)
        print("User Management")
        print("=" * 40)
        print("1. List users")
        print("2. Add new user")
        print("3. Remove user")
        print("4. Change password")
        print("5. Block user (force logout)")
        print("6. Unblock user")
        print("7. Show user status")
        print("8. Exit")
        print("-" * 40)
        
        choice = input("Select an option (1-8): ").strip()
        
        if choice == '1':
            list_users()
        elif choice == '2':
            add_new_user()
        elif choice == '3':
            remove_user()
        elif choice == '4':
            change_user_password()
        elif choice == '5':
            block_user_interactive()
        elif choice == '6':
            unblock_user_interactive()
        elif choice == '7':
            show_user_status()
        elif choice == '8':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    main()
