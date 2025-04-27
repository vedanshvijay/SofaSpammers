#!/bin/bash
echo "Creating OfficeIPMess Installer..."
echo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
pip install cx_Freeze

# Create the executable
python3 setup.py build

echo
echo "Installer created successfully!"
echo "You can find the executable in the build folder." 