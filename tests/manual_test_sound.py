# manual_test_sound.py
import subprocess
import os

# Standard Ubuntu sound path
SOUND_FILE = "/usr/share/sounds/freedesktop/stereo/message.oga"

print(f"Testing sound playback: {SOUND_FILE}")
try:
    if os.path.exists(SOUND_FILE):
        # paplay is the command-line tool for PulseAudio
        subprocess.run(["paplay", SOUND_FILE], check=True)
        print("Playback successful.")
    else:
        print("Default sound file not found. Trying system beep...")
        subprocess.run(["beep"], check=True)
except Exception as e:
    print(f"Playback failed: {e}")
    print("Tip: Install dependencies with 'sudo apt install pulseaudio-utils'")