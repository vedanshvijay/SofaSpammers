import json
import os
from security import SecurityManager
import time
import flet as ft

class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.messages_file = "messages.json"
        self.security = SecurityManager()
        
        # Initialize files if they don't exist
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w") as f:
                json.dump({}, f)
        
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, "w") as f:
                json.dump([], f)
    
    def register_user(self, username, password):
        # Validate input
        valid, message = self.security.validate_username(username)
        if not valid:
            return False, message
            
        valid, message = self.security.validate_password(password)
        if not valid:
            return False, message
        
        with open(self.users_file, "r") as f:
            users = json.load(f)
        
        if username in users:
            return False, "Username already exists"
        
        # Hash password with Argon2
        users[username] = self.security.hash_password(password)
        
        with open(self.users_file, "w") as f:
            json.dump(users, f)
        
        return True, "User registered successfully"
    
    def authenticate_user(self, username, password):
        with open(self.users_file, "r") as f:
            users = json.load(f)
        
        if username not in users:
            return False, "User does not exist"
        
        # Verify password with Argon2
        if not self.security.verify_password(password, users[username]):
            return False, "Incorrect password"
        
        return True, "Authentication successful"
    
    def save_message(self, sender, receiver, message):
        print("Saving message:", message, "type:", type(message))
        
        # Read existing messages
        with open(self.messages_file, "r") as f:
            messages = json.load(f)
        
        if not isinstance(message, str):
            message = str(message)
        
        # Encrypt message with Fernet
        encrypted_message = self.security.encrypt_message(message)
        
        # Check for duplicates by comparing content and timestamps within last 1 second
        current_time = time.time()
        for existing_msg in reversed(messages):
            # If same sender and receiver pair
            if existing_msg["sender"] == sender and existing_msg["receiver"] == receiver:
                # If message was sent within the last 1 second, check content
                if current_time - existing_msg["timestamp"] < 1:
                    # Try decrypting to compare contents
                    try:
                        decrypted = self.security.decrypt_message(existing_msg["message"])
                        if decrypted == message:
                            print("Duplicate message detected, not saving")
                            return
                    except:
                        # If decryption fails, just continue
                        pass
        
        # Add new message
        messages.append({
            "sender": sender,
            "receiver": receiver,
            "message": encrypted_message,
            "timestamp": current_time
        })
        
        with open(self.messages_file, "w") as f:
            json.dump(messages, f)
    
    def get_messages(self, user1, user2=None):
        with open(self.messages_file, "r") as f:
            messages = json.load(f)
        
        filtered_messages = []
        for msg in messages:
            try:
                if user2:
                    # Get messages between two specific users
                    if (msg["sender"] == user1 and msg["receiver"] == user2) or \
                       (msg["sender"] == user2 and msg["receiver"] == user1):
                        # Make a copy of the message to avoid modifying the original
                        msg_copy = msg.copy()
                        # Try to decrypt message, handle any errors
                        try:
                            encrypted_content = msg["message"]
                            # Check if this looks like an encrypted message
                            if encrypted_content.startswith("gAAAAAB"):
                                msg_copy["message"] = self.security.decrypt_message(encrypted_content)
                            # If it doesn't look encrypted, keep it as is (might be already decrypted)
                        except Exception as e:
                            print(f"Error decrypting message: {e}")
                            msg_copy["message"] = "[Encrypted message]"
                        
                        filtered_messages.append(msg_copy)
                else:
                    # Get all messages for a user
                    if msg["sender"] == user1 or msg["receiver"] == user1:
                        # Make a copy of the message to avoid modifying the original
                        msg_copy = msg.copy()
                        # Try to decrypt message, handle any errors
                        try:
                            encrypted_content = msg["message"]
                            # Check if this looks like an encrypted message
                            if encrypted_content.startswith("gAAAAAB"):
                                msg_copy["message"] = self.security.decrypt_message(encrypted_content)
                            # If it doesn't look encrypted, keep it as is (might be already decrypted)
                        except Exception as e:
                            print(f"Error decrypting message: {e}")
                            msg_copy["message"] = "[Encrypted message]"
                        
                        filtered_messages.append(msg_copy)
            except Exception as e:
                print(f"Error processing message: {e}")
        
        # Sort messages by timestamp
        filtered_messages.sort(key=lambda x: x.get("timestamp", 0))
        
        return filtered_messages
    
    def get_all_users(self):
        with open(self.users_file, "r") as f:
            users = json.load(f)
        return list(users.keys())

    def get_hint_style(self):
        current_theme = ft.Theme.current().to_dict()
        return ft.TextStyle(color=ft.colors.with_opacity(0.5, current_theme["text_color"])) 