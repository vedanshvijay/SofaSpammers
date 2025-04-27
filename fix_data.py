import json
import os
from security import SecurityManager

def fix_message_data():
    """Fix message data to work with the current security system"""
    
    # Initialize security manager
    security = SecurityManager()
    
    # Check if messages.json exists
    if os.path.exists("messages.json"):
        try:
            # Load existing messages
            with open("messages.json", "r") as f:
                messages = json.load(f)
            
            # Create fixed messages list
            fixed_messages = []
            
            # Keep messages but re-encrypt them with current key
            for msg in messages:
                try:
                    # Try to get the message content safely
                    content = msg.get("message", "[No content]")
                    
                    # Create a new compatible message
                    new_msg = {
                        "sender": msg.get("sender", "unknown"),
                        "receiver": msg.get("receiver", "unknown"),
                        "message": security.encrypt_message(content if isinstance(content, str) else "[Recovered message]"),
                        "timestamp": msg.get("timestamp", os.path.getmtime("messages.json"))
                    }
                    
                    fixed_messages.append(new_msg)
                except Exception as e:
                    print(f"Skipping incompatible message: {e}")
            
            # Backup the original file
            if os.path.exists("messages.json") and not os.path.exists("messages.json.bak"):
                os.rename("messages.json", "messages.json.bak")
                print("Created backup of messages.json as messages.json.bak")
            
            # Save fixed messages
            with open("messages.json", "w") as f:
                json.dump(fixed_messages, f)
            
            print(f"✓ Fixed {len(fixed_messages)} messages successfully")
            return True
            
        except Exception as e:
            print(f"Error fixing messages: {e}")
            return False
    else:
        # Create empty messages file if it doesn't exist
        with open("messages.json", "w") as f:
            json.dump([], f)
        print("✓ Created new empty messages.json file")
        return True

def deduplicate_messages():
    """Remove duplicate messages from messages.json"""
    
    security = SecurityManager()
    
    if os.path.exists("messages.json"):
        try:
            # Load existing messages
            with open("messages.json", "r") as f:
                messages = json.load(f)
            
            print(f"Loaded {len(messages)} messages, checking for duplicates...")
            
            # Track unique messages by content hash
            unique_messages = []
            deduplicated = 0
            
            # Track seen message fingerprints (sender+receiver+content)
            seen_msgs = set()
            
            for msg in messages:
                sender = msg.get("sender", "unknown")
                receiver = msg.get("receiver", "unknown")
                encrypted = msg.get("message", "")
                timestamp = msg.get("timestamp", 0)
                
                # Try to decrypt to get content
                try:
                    content = security.decrypt_message(encrypted)
                    # Create fingerprint
                    fingerprint = f"{sender}:{receiver}:{content}"
                    
                    # If we've seen this message before, skip it
                    if fingerprint in seen_msgs:
                        deduplicated += 1
                        continue
                    
                    # Otherwise mark as seen and keep
                    seen_msgs.add(fingerprint)
                    unique_messages.append(msg)
                except:
                    # If can't decrypt, just keep the message
                    unique_messages.append(msg)
            
            # Backup the original file
            if os.path.exists("messages.json") and not os.path.exists("messages.json.bak"):
                os.rename("messages.json", "messages.json.bak")
                print("Created backup of messages.json as messages.json.bak")
            
            # Save deduplicated messages
            with open("messages.json", "w") as f:
                json.dump(unique_messages, f)
            
            print(f"✓ Removed {deduplicated} duplicate messages, saved {len(unique_messages)} unique messages")
            return True
            
        except Exception as e:
            print(f"Error deduplicating messages: {e}")
            return False
    else:
        print("No messages.json file found")
        return False

if __name__ == "__main__":
    print("Fixing message data compatibility...")
    if fix_message_data():
        print("\nFixed data compatibility! Now deduplicating messages...")
        if deduplicate_messages():
            print("\nAll done! Now you can run the application with 'python main.py'")
        else:
            print("\nFailed to deduplicate messages")
    else:
        print("\nFailed to fix data. You may need to reset data with 'python reset_data.py'") 