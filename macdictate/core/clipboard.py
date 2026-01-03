import Cocoa
import logging
import time

logger = logging.getLogger(__name__)

class ClipboardManager:
    """
    Manages the system clipboard (NSPasteboard) to allow saving and restoring state.
    This ensures that injecting text via copy-paste doesn't destroy the user's existing clipboard content.
    """
    
    @staticmethod
    def snapshot():
        """
        Captures the current state of the general pasteboard.
        
        Returns:
            list: A list of dicts, where each dict represents an item and contains its data for all available types.
                  Returns None if the clipboard is empty or cannot be read.
        """
        try:
            pb = Cocoa.NSPasteboard.generalPasteboard()
            items = pb.pasteboardItems()
            
            if not items:
                logger.debug("Clipboard snapshot: Empty clipboard.")
                return []
            
            snapshot_data = []
            
            for item in items:
                item_data = {}
                types = item.types()
                
                for type_name in types:
                    # We capture the data for every type available for this item
                    data = item.dataForType_(type_name)
                    if data:
                        item_data[type_name] = data
                
                if item_data:
                    snapshot_data.append(item_data)
            
            logger.debug(f"Clipboard snapshot: Captured {len(snapshot_data)} items.")
            return snapshot_data
            
        except Exception as e:
            logger.error(f"Clipboard snapshot failed: {e}", exc_info=True)
            return None

    @staticmethod
    def restore(snapshot_data):
        """
        Restores the clipboard to the state captured in the snapshot.
        
        Args:
            snapshot_data: The data structure returned by snapshot().
        """
        if snapshot_data is None:
            return

        try:
            logger.debug(f"Clipboard restore: Restoring {len(snapshot_data)} items...")
            pb = Cocoa.NSPasteboard.generalPasteboard()
            pb.clearContents()
            
            for item_data in snapshot_data:
                # Create a new pasteboard item
                item = Cocoa.NSPasteboardItem.alloc().init()
                
                # Add all types and data to this item
                for type_name, data in item_data.items():
                    item.setData_forType_(data, type_name)
                    
                # Write the item to the pasteboard
                pb.writeObjects_([item])
            
            logger.debug("Clipboard restore: Complete.")
                
        except Exception as e:
            logger.error(f"Clipboard restore failed: {e}", exc_info=True)
