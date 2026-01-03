import Quartz
import time
import logging

logger = logging.getLogger(__name__)

class FastTyper:
    """
    Universally injects text by simulating hardware keyboard events at the OS level.
    Uses CGEventKeyboardSetUnicodeString to type characters without relying on Accessibility APIs.
    """
    
    @staticmethod
    def type_text(text: str, chunk_size: int = 20, delay: float = 0.002) -> bool:
        """
        Types text by posting keyboard events with Unicode payloads.
        
        Args:
            text: The string to type.
            chunk_size: Number of characters to attach to each event.
            delay: Safety sleep (in seconds) between chunks to prevent buffer overflows.
            
        Returns:
            bool: True if events were successfully posted, False otherwise.
        """
        if not text:
            return True
            
        try:
            # We use a dummy keycode (0) because the character codes are what matter.
            # 0 is 'a' on ANSI keyboards, but the Unicode string overrides it.
            # We need to create a discrete event for the system to attach the string to.
            
            # The strategy:
            # 1. Create a "null" keyboard event (keydown).
            # 2. Attach a chunk of unicode string to it.
            # 3. Post it.
            # 4. Create a corresponding keyup event (optional, but good practice).
            
            # Note: CGEventKeyboardSetUnicodeString handles the string mapping.
            
            text_len = len(text)
            logger.debug(f"FastTyper: Typing {text_len} chars in chunks of {chunk_size}...")
            
            for i in range(0, text_len, chunk_size):
                chunk = text[i : i + chunk_size]
                chunk_len = len(chunk)
                
                # Create a sterile key-down event
                # 0 = Virtual key code (ignored because we set string)
                # True = Key down
                event_source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
                key_down = Quartz.CGEventCreateKeyboardEvent(event_source, 0, True)
                
                # Set the unicode string for this event
                Quartz.CGEventKeyboardSetUnicodeString(key_down, chunk_len, chunk)
                
                # Post the event to the HID system
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                
                # Sleep briefly to let the target app process the chunk
                if delay > 0:
                    time.sleep(delay)
            
            logger.debug("FastTyper: Completed.")
            return True
            
        except Exception as e:
            logger.error(f"FastTyper failed: {e}", exc_info=True)
            return False
