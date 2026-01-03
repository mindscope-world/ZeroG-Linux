#!/bin/bash

# --- ZeroG Startup Wrapper ---
# This script is designed to be used with macOS Automator to run 
# ZeroG in the background as a "Service".

# 1. Terminate any previous instances of the app
# 'pkill -f' stops any process with "main.py" in the name so we don't have two running.
# '|| true' means "don't fail if there wasn't an instance running already".
pkill -f "main.py" || true

# 2. Brief pause to ensure the microphone and system resources are fully released
sleep 0.5

# Path to your ZeroG project
PROJECT_DIR="/Users/antony/Documents/Projects/MacDictate"

# 1. Stop any existing instance
pkill -f "main.py" || true
sleep 0.5

# 2. Go to directory
cd "$PROJECT_DIR"

# 3. Launch quietly in background
nohup ./.venv/bin/python main.py >/dev/null 2>&1 &
