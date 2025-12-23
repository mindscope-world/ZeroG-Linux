#!/bin/bash

# --- MacDictate Setup Script ---
# This script sets up a "virtual environment" (a private folder for our Python plugins)
# and installs all the AI libraries needed to run the app.

echo "🎙️ Setting up MacDictate..."

# Step 1: Check if Python is installed on this Mac
# 'command -v python3' looks for the python command in the system.
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 not found. Please install Python 3.11+ from https://python.org"
    exit 1
fi

# Step 2: Create a virtual environment (folder named .venv)
# This keeps the MacDictate plugins separate from the rest of your computer.
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Step 3: Activate the virtual environment
# This tells the computer to use the plugins inside the .venv folder.
source .venv/bin/activate

# Step 4: Upgrade 'pip' (the Python plugin manager)
# It's always a good idea to have the latest version of pip.
echo "Upgrading pip..."
pip install --upgrade pip

# Step 5: Install all requirements
# This reads requirements.txt and downloads MLX Whisper, SoundDevice, etc.
echo "Installing dependencies (this may take a minute)..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo "To run MacDictate, use: source .venv/bin/activate && python main.py"
