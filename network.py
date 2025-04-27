import socket
import threading
import json
import time
import os
from security import SecurityManager

class NetworkManager:
    def __init__(self, username, key=None, message_callback=None):
        self.username = username
        self.security = SecurityManager()
        self.message_callback = message_callback
        self.running = False
        self.peers = {}  # {username: (ip, port)}
        self.server_socket = None
        self.server_thread = None
        self.server_port = int(os.getenv('DEFAULT_PORT', 8000))
        
    def start_server(self):
        """Start the server to listen for incoming messages"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Try to bind to the default port, if busy try the next one
        bound = False
        max_port = int(os.getenv('MAX_PORT', 8100))
        while not bound and self.server_port < max_port:
            try:
                self.server_socket.bind(('0.0.0.0', self.server_port))
                bound = True
            except OSError:
                self.server_port += 1
        
        if not bound:
            raise Exception("Could not find an available port")
        
        # Wrap socket with SSL if context is available
        ssl_context = self.security.get_ssl_context()
        if ssl_context:
            self.server_socket = ssl_context.wrap_socket(self.server_socket, server_side=True)
        
        self.server_socket.listen(5)
        self.running = True
        
        self.server_thread = threading.Thread(target=self._listen_for_connections)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        return self.server_port
    
    def _listen_for_connections(self):
        """Background thread to accept connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                time.sleep(0.1)
    
    def _handle_client(self, client_socket, address):
        """Handle a client connection"""
        try:
            # Receive the message
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete message
                if len(data) > 0 and data[-1] == ord('\n'):
                    break
            
            if not data:
                return
                
            # Decrypt and parse the message
            try:
                decrypted_data = self.security.decrypt_message(data.strip().decode())
                message = json.loads(decrypted_data)
                
                # Call the callback with the message
                if self.message_callback:
                    self.message_callback(message)
            except Exception as e:
                print(f"Error processing message: {e}")
        finally:
            client_socket.close()
    
    def send_message(self, recipient, message_content):
        """Send a message to a peer"""
        if recipient not in self.peers:
            return False, "Recipient not found"
            
        ip, port = self.peers[recipient]
        
        message = {
            "sender": self.username,
            "content": message_content,
            "timestamp": time.time()
        }
        
        # Encrypt the message
        encrypted_data = self.security.encrypt_message(json.dumps(message))
        
        try:
            # Create socket and wrap with SSL if context is available
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_context = self.security.get_ssl_context()
            if ssl_context:
                s = ssl_context.wrap_socket(s, server_side=False)
            
            s.settimeout(5)
            s.connect((ip, port))
            
            # Send the encrypted message
            s.sendall(encrypted_data.encode() + b'\n')
            
            # Close the connection
            s.close()
            
            return True, "Message sent"
        except Exception as e:
            return False, f"Failed to send message: {e}"
    
    def add_peer(self, username, ip, port):
        """Add a peer to the list of known peers"""
        self.peers[username] = (ip, port)
    
    def remove_peer(self, username):
        """Remove a peer from the list of known peers"""
        if username in self.peers:
            del self.peers[username]
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None 