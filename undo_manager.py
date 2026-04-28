import os
import shutil
from send2trash import send2trash
import utils

logger = utils.setup_logger(__name__)

class UndoManager:
    def __init__(self):
        self.history = []

    def push(self, reverse_action: dict):
        if reverse_action:
            self.history.append(reverse_action)

    def undo(self) -> str:
        if not self.history:
            return "There is nothing to undo."
            
        action = self.history.pop()
        type = action.get("action")
        
        try:
            if type == "delete_folder":
                send2trash(action.get("path"))
                return "Folder deleted."
            elif type == "delete_file":
                send2trash(action.get("path"))
                return "File deleted."
            elif type == "restore_recycle_bin":
                return self._restore_from_recycle_bin(action)
            elif type == "move_file_back":
                shutil.move(action.get("from"), action.get("to"))
                return "File moved back."
            elif type == "rename_file_back":
                os.rename(action.get("old_path"), action.get("new_path"))
                return "File renamed back."
            elif type == "delete_shortcut":
                send2trash(action.get("path"))
                return "Shortcut deleted."
            elif type == "arrange_back":
                moves = action.get("moves", [])
                for move in moves:
                    shutil.move(move["from"], move["to"])
                return "Files arranged back."
            else:
                return "Unknown undo action."
        except Exception as e:
            logger.error(f"Error undoing {type}: {e}")
            return f"Failed to undo: {str(e)}"

    def _restore_from_recycle_bin(self, action):
        target_name = action.get("name")
        if not target_name:
            return "Cannot undo: missing filename info."
            
        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            recycle_bin = shell.NameSpace(10)
            
            restored = False
            for item in recycle_bin.Items():
                if item.Name == target_name:
                    for verb in item.Verbs():
                        verb_name = verb.Name.lower().replace("&", "")
                        if "restore" in verb_name or "wiederherstellen" in verb_name:
                            verb.DoIt()
                            restored = True
                            break
                    if restored:
                        break
                        
            if restored:
                return f"Restored '{target_name}' from Recycle Bin."
            else:
                return f"Could not find '{target_name}' in Recycle Bin."
                
        except Exception as e:
            logger.error(f"Recycle Bin restore error: {e}")
            return f"Failed to restore from Recycle Bin: {str(e)}"

