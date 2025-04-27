import os
import sys
import subprocess
import json
from cx_Freeze import setup, Executable

def check_requirements():
    """Check if all required packages are installed"""
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read().splitlines()
        
        for req in requirements:
            if req:
                try:
                    __import__(req.split(">=")[0].split("==")[0])
                except ImportError:
                    print(f"Installing missing requirement: {req}")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        
        return True
    except Exception as e:
        print(f"Error checking requirements: {e}")
        return False

def initialize_files():
    """Initialize necessary files"""
    # Create empty peers file if it doesn't exist
    if not os.path.exists("peers.json"):
        with open("peers.json", "w") as f:
            json.dump({}, f)
    
    # Initialize empty message and user files if they don't exist
    if not os.path.exists("messages.json"):
        with open("messages.json", "w") as f:
            json.dump([], f)
    
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)

def main():
    """Main setup function"""
    print("Setting up Office IP Messenger...")
    
    if check_requirements():
        print("Requirements check passed.")
    else:
        print("Failed to check requirements.")
        return
    
    initialize_files()
    print("Files initialized.")
    
    print("Setup complete! You can now run the application with 'python main.py'")
    
    # Ask if user wants to run the application now
    run_now = input("Do you want to run the application now? (y/n): ").lower()
    if run_now == 'y' or run_now == 'yes':
        subprocess.call([sys.executable, "main.py"])

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["flet", "cryptography", "PIL", "argon2", "dotenv", "fastapi", "uvicorn", "httpx", "websockets", "playsound"],
    "include_files": [
        "assets/",
        "notification.wav",
        "users.json",
        "peers.json"
    ]
}

# GUI applications require a different base on Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="OfficeIPMess",
    version="1.0",
    description="Office IP Messaging Application",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="OfficeIPMess.exe",
            icon="assets/icon.ico"  # You'll need to create this icon file
        )
    ]
)

if __name__ == "__main__":
    main() 