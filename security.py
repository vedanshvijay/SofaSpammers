import os
import re
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import ssl

# Load environment variables
load_dotenv()

class SecurityManager:
    def __init__(self):
        # Initialize password hasher
        self.ph = PasswordHasher()
        
        # Load or generate encryption key
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
        self.cipher = Fernet(self.encryption_key.encode())
        
        # SSL context
        self.ssl_context = None
        cert_path = os.getenv('SSL_CERT_PATH')
        key_path = os.getenv('SSL_KEY_PATH')
        if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(cert_path, key_path)
    
    def hash_password(self, password):
        """Hash password using Argon2"""
        return self.ph.hash(password)
    
    def verify_password(self, password, hash):
        """Verify password against hash"""
        try:
            return self.ph.verify(hash, password)
        except:
            return False
    
    def encrypt_message(self, message):
        """Encrypt message using Fernet"""
        return self.cipher.encrypt(message.encode()).decode()
    
    def decrypt_message(self, encrypted_message):
        """Decrypt message using Fernet"""
        return self.cipher.decrypt(encrypted_message.encode()).decode()
    
    def validate_username(self, username):
        """Validate username format"""
        if not username:
            return False, "Username cannot be empty"
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 20:
            return False, "Username must be at most 20 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""
    
    def validate_password(self, password):
        """Validate password strength"""
        if not password:
            return False, "Password cannot be empty"
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[^A-Za-z0-9]', password):
            return False, "Password must contain at least one special character"
        return True, ""
    
    def get_ssl_context(self):
        """Get SSL context for secure connections"""
        return self.ssl_context 