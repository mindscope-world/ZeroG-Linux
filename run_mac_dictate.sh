#!/bin/bash

# --- MacDictate Startup Wrapper ---
# This script is designed to be used with macOS Automator to run 
# MacDictate in the background as a "Service".

# 1. Terminate any previous instances of the app
# 'pkill -f' stops any process with "main.py" in the name so we don't have two running.
# '|| true' means "don't fail if there wasn't an instance running already".
pkill -f "main.py" || true

# 2. Brief pause to ensure the microphone and system resources are fully released
sleep 0.5

# 3. Navigate into the folder where the project lives
# Note: You may need to change this path if you move the project.
cd "/Users/antony/Documents/Projects/MacDictate"

# 4. Launch the application in the background
# 'nohup' stands for "No Hang Up" - it keeps the app running even if you close the terminal.
# '>/dev/null 2>&1' hides all the technical status messages.
# '&' tells the computer to run it in the background immediately.
# We use the full path to the Python installed in our environment (.venv).
nohup /Users/antony/Documents/Projects/MacDictate/.venv/bin/python3 main.py >/dev/null 2>&1 &
