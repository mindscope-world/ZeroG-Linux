import sys
import time
from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np

print("🛰️  Starting Pure-Terminal Debug...")

try:
    print("🛠️  Step 1: Checking Audio Device...")
    devices = sd.query_devices()
    print(f"✅ Found {len(devices)} audio devices.")
    
    print("🛠️  Step 2: Loading Whisper 'tiny' on CPU...")
    # Using 'tiny' and 'float32' as the most basic/compatible settings
    model = WhisperModel("tiny", device="cpu", compute_type="float32")
    print("✅ Whisper Model Loaded Successfully.")
    
    print("🛠️  Step 3: Running Warmup Inference...")
    warmup_audio = np.zeros(16000, dtype=np.float32)
    segments, _ = model.transcribe(warmup_audio)
    list(segments) # Force execution
    print("✅ Inference Warmup Success.")
    
    print("\n🚀 ALL SYSTEMS GO. Your hardware is compatible.")

except Exception as e:
    print("\n❌ DEBUG FAILED!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")
    sys.exit(1)