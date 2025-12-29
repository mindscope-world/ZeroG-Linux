import subprocess

SOUND_FILE = "/System/Library/Sounds/Pop.aiff"

print(f"Testing sound playback: {SOUND_FILE}")
try:
    subprocess.run(["afplay", SOUND_FILE], check=True)
    print("Playback successful.")
except Exception as e:
    print(f"Playback failed: {e}")
