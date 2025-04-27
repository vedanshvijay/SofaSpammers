import os
import json

def reset_data():
    """Reset all application data by clearing users, messages, and peers."""
    
    # Reset users
    with open("users.json", "w") as f:
        json.dump({}, f)
    print("✓ Users data cleared")
    
    # Reset messages
    with open("messages.json", "w") as f:
        json.dump([], f)
    print("✓ Messages data cleared")
    
    # Reset peers
    if os.path.exists("peers.json"):
        with open("peers.json", "w") as f:
            json.dump({}, f)
        print("✓ Peers data cleared")
    
    print("\nAll data has been reset. You can register new users now.")

if __name__ == "__main__":
    confirm = input("This will delete ALL users and messages. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        reset_data()
    else:
        print("Operation cancelled.") 