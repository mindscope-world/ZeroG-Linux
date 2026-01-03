import sys
import time
import threading
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from zerog.core.typer import FastTyper
from zerog.core.clipboard import ClipboardManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def test_fast_typer():
    logger.info("Testing FastTyper...")
    print("\n--- FastTyper Test ---")
    print("Focus on a text field (e.g. this terminal) in 3 seconds to see typed output...")
    time.sleep(3)
    
    text = "Hello from FastTyper! 🚀 (Universal Injection)"
    success = FastTyper.type_text(text)
    
    if success:
        logger.info("FastTyper commands posted successfully.")
    else:
        logger.error("FastTyper failed.")

def test_clipboard_preservation():
    logger.info("Testing Clipboard Preservation...")
    print("\n--- Clipboard Manager Test ---")
    
    # 1. User manually copies something (optional, but we can simulate it)
    print("Please copy some text or a file to your clipboard NOW.")
    print("Waiting 5 seconds for you to copy something...")
    time.sleep(5)
    
    # 2. Snapshot
    logger.info("Taking snapshot...")
    snapshot = ClipboardManager.snapshot()
    logger.info(f"Snapshot taken. Items: {len(snapshot) if snapshot else 0}")
    
    # 3. Clobber clipboard
    import Cocoa
    pb = Cocoa.NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.writeObjects_(["CLOBBERED CONTENT"])
    logger.info("Clipboard clobbered with 'CLOBBERED CONTENT'. Verify manually if you want (Cmd+V).")
    time.sleep(2)
    
    # 4. Restore
    logger.info("Restoring clipboard...")
    ClipboardManager.restore(snapshot)
    logger.info("Clipboard restored. Try pasting now to verify your original content is back.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "typer":
        test_fast_typer()
    elif len(sys.argv) > 1 and sys.argv[1] == "clipboard":
        test_clipboard_preservation()
    else:
        print("Usage: python tests/verify_injection.py [typer|clipboard]")
