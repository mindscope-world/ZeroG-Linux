#!/bin/bash
set -e

echo "🛰️ Initializing ZeroG Linux Flight Prep..."

# 1. Install System dependencies
echo "📦 Installing system dependencies (xdotool, xclip, portaudio)..."
sudo apt update
sudo apt install -y xdotool xclip libportaudio2 libatlas-base-dev

# 2. Create Virtual Environment
echo "🧪 Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python requirements
echo "🐍 Installing Python packages..."
pip install --upgrade pip
pip install faster-whisper sounddevice numpy pyperclip pynput google-genai python-dotenv

# 4. Set Permissions
echo "🔑 Adjusting user permissions for input/audio..."
# Adding user to groups so sudo isn't required for keyboard/mic
sudo usermod -aG input $USER
sudo usermod -aG audio $USER

echo "✅ Pre-flight complete. Please REBOOT your machine for group changes to take effect."
echo "🚀 To launch: ./run_zerog.sh"

# 5. Generate Visual Assets
echo "🎨 Generating UI assets..."
python3 generate_assets.py

echo "✅ Pre-flight complete. Please REBOOT for group changes to take effect."