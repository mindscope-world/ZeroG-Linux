# tests/verify_injection.py
import sys
import time
import logging
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from zerog.core.typer import FastTyper, ClipboardManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Verification")

def check_dependencies():
    """Ensure required Linux CLI tools are installed."""
    for tool in ["xdotool", "xclip"]:
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            logger.error(f"Missing dependency: {tool}. Please run: sudo apt install {tool}")
            return False
    return True

def test_fast_injection():
    logger.info("Testing FastTyper Injection (Snapshot -> Copy -> Paste -> Restore)...")
    print("\n--- FastTyper Linux Test ---")
    print("Focus on a text field (e.g. this terminal) in 3 seconds...")
    time.sleep(3)
    
    text = "Hello from ZeroG Linux! 🚀 (X11 Injection)"
    # On Linux, FastTyper.inject handles the full logic
    success = FastTyper.inject(text)
    
    if success:
        logger.info("Injection sequence completed successfully.")
    else:
        logger.error("Injection failed. Check if xdotool and xclip are installed.")

def test_clipboard_preservation():
    logger.info("Testing Clipboard Preservation (using pyperclip/xclip)...")
    print("\n--- Clipboard Manager Test ---")
    
    print("Action Required: Please copy some text to your clipboard NOW.")
    print("Waiting 5 seconds for you to copy...")
    time.sleep(5)
    
    # 2. Snapshot
    logger.info("Taking snapshot of your current clipboard...")
    snapshot = ClipboardManager.snapshot()
    logger.info(f"Captured: '{snapshot}'" if snapshot else "Clipboard was empty.")
    
    # 3. Clobber clipboard
    import pyperclip
    pyperclip.copy("--- CLOBBERED BY ZEROG ---")
    logger.info("Clipboard overwritten. If you paste now, you will see the clobber text.")
    time.sleep(3)
    
    # 4. Restore
    logger.info("Restoring original content...")
    ClipboardManager.restore(snapshot)
    logger.info("✅ Restored! Try pasting now to verify your original content is back.")

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
        
    if len(sys.argv) > 1 and sys.argv[1] == "typer":
        test_fast_injection()
    elif len(sys.argv) > 1 and sys.argv[1] == "clipboard":
        test_clipboard_preservation()
    else:
        print("Usage: python tests/verify_injection.py [typer|clipboard]")