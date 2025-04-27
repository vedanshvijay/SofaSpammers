import json
import os
from security import SecurityManager
import time

def repair_messages():
    """Repair messages - make sure all messages are properly encrypted"""
    
    # Initialize security manager
    security = SecurityManager()
    
    # Check if messages.json exists
    if os.path.exists("messages.json"):
        try:
            # Load existing messages
            with open("messages.json", "r") as f:
                messages = json.load(f)
            
            print(f"Loaded {len(messages)} messages, repairing...")
            
            # Track fixed messages
            fixed_messages = []
            fixed_count = 0
            
            for msg in messages:
                sender = msg.get("sender", "unknown")
                receiver = msg.get("receiver", "unknown")
                content = msg.get("message", "")
                timestamp = msg.get("timestamp", 0)
                
                try:
                    # Check if message is properly encrypted (starts with gAAAAAB and is long enough)
                    if content.startswith("gAAAAAB") and len(content) > 50:
                        # This is likely a properly encrypted message, try to decrypt it to verify
                        try:
                            decrypted = security.decrypt_message(content)
                            # Keep the original encrypted content if decryption worked
                            fixed_messages.append(msg)
                        except Exception as e:
                            print(f"Failed to decrypt message, re-encrypting: {e}")
                            # If decryption fails, re-encrypt with a placeholder
                            fixed_msg = {
                                "sender": sender,
                                "receiver": receiver,
                                "message": security.encrypt_message("[Message could not be recovered]"),
                                "timestamp": timestamp
                            }
                            fixed_messages.append(fixed_msg)
                            fixed_count += 1
                    else:
                        # Not encrypted or shorter encryption - re-encrypt it
                        print(f"Re-encrypting message from {sender} to {receiver}: {content[:30]}...")
                        fixed_msg = {
                            "sender": sender,
                            "receiver": receiver,
                            "message": security.encrypt_message(content),
                            "timestamp": timestamp
                        }
                        fixed_messages.append(fixed_msg)
                        fixed_count += 1
                except Exception as e:
                    print(f"Error processing message: {e}")
                    # Keep the original if there's an error
                    fixed_messages.append(msg)
            
            # Backup the original file
            backup_name = "messages.json.bak-" + str(int(time.time()))
            os.rename("messages.json", backup_name)
            print(f"Created backup of messages.json as {backup_name}")
            
            # Save fixed messages
            with open("messages.json", "w") as f:
                json.dump(fixed_messages, f)
            
            print(f"✓ Fixed {fixed_count} messages, saved {len(fixed_messages)} total messages")
            return True
            
        except Exception as e:
            print(f"Error fixing messages: {e}")
            return False
    else:
        print("No messages.json file found")
        return False

if __name__ == "__main__":
    print("Repairing message database...")
    if repair_messages():
        print("\nAll done! Now you can run the application with 'python main.py'")
    else:
        print("\nFailed to repair messages. Please check your database.") 