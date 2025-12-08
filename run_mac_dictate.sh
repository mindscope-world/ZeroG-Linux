#!/bin/bash

# 1. Terminate existing instances
# The '-f' flag matches the full command line (e.g., "dictate_mlx.py")
# '|| true' prevents Automator from throwing an error if the app wasn't running
pkill -f "main.py" || true

# 2. Brief pause to ensure the microphone and ports are fully released
sleep 0.5

# 3. Navigate to project directory
cd "/Users/antony/Documents/Projects/MacDictate"

# 4. Launch the application in the background
# 'nohup' keeps it running even when Automator closes
# '&' puts it in the background so the Automator icon stops bouncing immediately
# using absolute path to python environment to avoid shim issues
nohup /Users/antony/.pyenv/versions/3.11.9/bin/python3 main.py >/dev/null 2>&1 &
