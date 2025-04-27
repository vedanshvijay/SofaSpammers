# Sofa Spammers 🛋️

A modern, secure messaging app for your local network. Perfect for office communication, team collaboration, or just sharing memes with your coworkers.

## Project Structure
```
officeipmess/
├── assets/               # Application assets (icons, images)
├── main.py              # Main application file
├── comm_server.py       # Communication server
├── comm_client.py       # Communication client
├── database.py          # Database operations
├── security.py          # Security operations
├── requirements.txt     # Python dependencies
├── notification.wav     # Notification sound file
├── README.md           # Documentation
└── LICENSE             # License information
```

## Tech Stack

- **Frontend**: Flet (>=0.10.0)
- **Backend**: FastAPI (>=0.68.0) + Uvicorn (>=0.15.0)
- **Security**: Cryptography (>=40.0.0), Argon2-cffi (>=23.1.0)
- **Media**: Pillow (>=9.5.0), Playsound (==1.2.2)
- **Networking**: HTTPX, WebSockets (>=10.0)
- **Storage**: JSON-based file system
- **Environment**: Python 3.x

## Features

- **Real-time messaging**: Instant communication without the wait
- **File sharing**: Share files and memes at lightning speed
- **Audio notifications**: Stay on top of important messages
- **End-to-end encryption**: Your conversations stay private
- **Dark/light theme support**: Choose your preferred style
- **User authentication**: Secure access control

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/officeipmess.git
   cd officeipmess
   ```

2. **Create virtual environment**:
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt --no-cache-dir
   ```

4. **Start the server** (in Terminal 1):
   ```bash
   # IMPORTANT: Activate virtual environment in this terminal first
   source venv/bin/activate  # (macOS/Linux)
   venv\Scripts\activate     # (Windows)
   
   python comm_server.py
   ```

5. **Run the application** (in Terminal 2):
   ```bash
   # IMPORTANT: You must activate the virtual environment in this new terminal
   source venv/bin/activate  # (macOS/Linux)
   venv\Scripts\activate     # (Windows)
   
   python main.py
   ```

## Terminal Management

### Multiple Terminal Requirements
The application requires two separate terminals to run properly:

1. **Server Terminal**:
   - Must have virtual environment activated
   - Must have all dependencies installed
   - Runs the server process

2. **Client Terminal**:
   - Must be a separate terminal window
   - Must have virtual environment activated
   - Must have all dependencies installed
   - Runs the client application

### Terminal Setup Checklist
Before running the application, ensure:

1. Both terminals have:
   - Virtual environment activated
   - All dependencies installed
   - Correct Python version
   - Proper permissions

2. Activation sequence:
   ```bash
   # For each new terminal:
   cd officeipmess
   source venv/bin/activate  # (macOS/Linux)
   venv\Scripts\activate     # (Windows)
   ```

3. Verify installation:
   ```bash
   # In each terminal, verify dependencies
   pip list
   ```

## Initial Setup

After cloning and installing, you'll need to:

1. **Set up the environment**:
   - The app will create necessary JSON files on first run
   - Default port is 8001 (can be changed in comm_server.py)

2. **First Run**:
   - Register a new user when first launching the app
   - The first user will be created as an admin
   - Server must be running before starting the client

3. **File Permissions**:
   - Ensure write permissions in the app directory
   - Audio notifications require read access to notification.wav

## Installation

### Prerequisites
- Python 3.x (3.8 or higher recommended)
- pip (Python package manager)
- Virtual environment support
- Terminal/Command Prompt access

### Clean Installation Guide

1. **Create and prepare project directory**:
   ```bash
   # Create project directory (if not exists)
   mkdir officeipmess
   cd officeipmess
   ```

2. **Set up a fresh virtual environment**:
   ```bash
   # Remove existing venv if any
   rm -rf venv

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Verify Python Environment**:
   ```bash
   # Should show path inside your venv directory
   which python  # (macOS/Linux)
   where python  # (Windows)
   ```

4. **Install dependencies**:
   ```bash
   # Upgrade pip first
   python -m pip install --upgrade pip

   # Install all dependencies
   pip install -r requirements.txt --no-cache-dir
   ```

5. **Start the server**:
   ```bash
   python comm_server.py
   ```

6. **Run the application** (in a new terminal):
   ```bash
   # Don't forget to activate venv in the new terminal
   source venv/bin/activate  # (macOS/Linux)
   venv\Scripts\activate     # (Windows)
   
   python main.py
   ```

## Common Issues and Solutions

### 1. ModuleNotFoundError (e.g., "No module named 'fastapi'")

This usually happens when:
- The virtual environment isn't activated
- Dependencies weren't installed correctly
- Wrong Python interpreter is being used

**Solution**:
```bash
# 1. Verify you're in the virtual environment
which python  # (macOS/Linux)
where python  # (Windows)
# Should show path ending in venv/bin/python

# 2. If not in venv or unsure, recreate it:
deactivate  # (if venv is active)
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # (macOS/Linux)
venv\Scripts\activate     # (Windows)

# 3. Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 2. Dependency Conflicts

If you see version conflicts or dependency errors:

```bash
# Clear pip cache and reinstall
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### 3. Virtual Environment Issues

If your virtual environment isn't working correctly:

```bash
# 1. Deactivate current environment
deactivate

# 2. Remove existing environment
rm -rf venv

# 3. Create new environment with specific Python version
python3.8 -m venv venv  # or python3.9, python3.10, etc.

# 4. Activate and verify
source venv/bin/activate  # (macOS/Linux)
venv\Scripts\activate     # (Windows)
python --version
```

### 4. Server Won't Start

If the server fails to start:
- Ensure port 8001 is not in use
- Check if you have proper permissions
- Verify all dependencies are installed

```bash
# Check if port is in use (macOS/Linux)
lsof -i :8001

# Kill process using the port if needed
kill -9 <PID>
```