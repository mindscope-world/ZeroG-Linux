# zerog/core/typer.py
"""
Linux doesn't have a unified "System Events" framework like macOS, 
the most reliable way to inject text on Ubuntu is to combine a clipboard manager (using xclip) 
with a keystroke simulator (xdotool).

xdotool: Handles the keyboard simulation (the 'V' in Ctrl+V)
xclip: Allows pyperclip to interact with the Linux clipboard
"""
import subprocess
import time
import pyperclip
import logging
import threading

logger = logging.getLogger(__name__)

class ClipboardManager:
    """Linux implementation for clipboard state management using xclip."""
    
    @staticmethod
    def snapshot():
        """Captures the current clipboard content using pyperclip."""
        try:
            return pyperclip.paste()
        except Exception as e:
            logger.error(f"Clipboard snapshot failed: {e}")
            return ""

    @staticmethod
    def restore(text_data):
        """Restores the clipboard to a previous string state."""
        try:
            if text_data:
                pyperclip.copy(text_data)
                logger.debug("Clipboard restored.")
        except Exception as e:
            logger.error(f"Clipboard restore failed: {e}")

class FastTyper:
    """
    Linux-native text injector.
    Strategy: Copy text to clipboard -> Trigger Ctrl+V via xdotool -> Restore clipboard.
    """
    
    @staticmethod
    def inject(text: str) -> bool:
        """
        The primary injection entry point for Linux.
        """
        if not text:
            return True

        logger.info(f"FastTyper: Injecting {len(text)} characters.")

        try:
            # 1. Snapshot the user's current work
            original_content = ClipboardManager.snapshot()

            # 2. Stage the new transcription
            pyperclip.copy(text)
            
            # 3. Small delay to ensure the OS clipboard manager registers the change
            time.sleep(0.1)

            # 4. Use xdotool to simulate the paste command
            # This works across almost all Linux GUI apps (Browsers, IDEs, Slack, etc.)
            subprocess.run([
                "xdotool", "key", "ctrl+v"
            ], check=True)

            # 5. Restore the original clipboard in a background thread 
            # to prevent blocking the UI, with enough delay for the paste to finish.
            threading.Timer(0.8, lambda: ClipboardManager.restore(original_content)).start()
            
            return True

        except subprocess.CalledProcessError:
            logger.error("xdotool command failed. Is it installed?")
            return False
        except Exception as e:
            logger.error(f"Injection failed: {e}", exc_info=True)
            return False

    @staticmethod
    def type_text(text: str):
        """
        Alternative 'Slow' typing mode if paste is blocked.
        Simulates individual keystrokes.
        """
        try:
            subprocess.run(["xdotool", "type", "--delay", "5", text], check=True)
        except Exception as e:
            logger.error(f"Slow typing failed: {e}")