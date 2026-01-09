#!/bin/bash

# 1. Navigate to the project directory (optional, but good practice)
cd "$(dirname "$0")"

# 2. Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: Virtual environment (venv) not found."
    exit 1
fi

# 3. Force X11/XCB to prevent the GUI from disappearing on Ubuntu 24.04
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb
export QT_XCB_GL_INTEGRATION=none

# 4. Optional: Fix scaling for high-resolution Lenovo screens
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# 5. Launch the application
echo "🛰️ ZeroG is launching..."
python3 main.py