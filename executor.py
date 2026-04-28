import os
import shutil
import hashlib
import datetime
from send2trash import send2trash
import win32com.client
import utils
from everything_api import EverythingAPI
from tag_manager import TagManager

logger = utils.setup_logger(__name__)

class ActionExecutor:
    def __init__(self):
        try:
            self.search_api = EverythingAPI()
        except:
            self.search_api = None
        self.tag_manager = TagManager()

    def execute_action(self, action_json: dict) -> dict:
        """
        Executes a filesystem action and returns a result dict.
        result = {
            "success": bool,
            "message": str,
            "reverse_action": dict # Instructions for undo_manager
        }
        """
        action = action_json.get("action")
        logger.info(f"Executing action: {action}")
        
        try:
            if action == "create_folder":
                return self._create_folder(action_json)
            elif action == "create_file":
                return self._create_file(action_json)
            elif action == "delete_folder":
                return self._delete_folder(action_json)
            elif action == "delete_file":
                return self._delete_file(action_json)
            elif action == "restore_recycle_bin":
                return self._restore_recycle_bin(action_json)
            elif action == "move_file":
                return self._move_file(action_json)
            elif action == "rename_file":
                return self._rename_file(action_json)
            elif action == "create_shortcut":
                return self._create_shortcut(action_json)
            elif action == "arrange_by_type":
                return self._arrange_by_type(action_json)
            elif action == "open_folder":
                return self._open_folder(action_json)
            elif action == "convert_file":
                return self._convert_file(action_json)
            elif action == "copy_file":
                return self._copy_file(action_json)
            elif action == "duplicate_file":
                return self._duplicate_file(action_json)
            elif action == "file_info":
                return self._file_info(action_json)
            elif action == "clean_empty":
                return self._clean_empty(action_json)
            elif action == "flatten_folder":
                return self._flatten_folder(action_json)
            elif action == "bulk_rename":
                return self._bulk_rename(action_json)
            elif action == "find_duplicates":
                return self._find_duplicates(action_json)
            elif action == "disk_usage":
                return self._disk_usage(action_json)
            elif action == "add_tag":
                return self._add_tag(action_json)
            elif action == "remove_tag":
                return self._remove_tag(action_json)
            elif action == "search_by_tag":
                return self._search_by_tag(action_json)
            elif action == "list_tags":
                return self._list_tags(action_json)
            elif action == "open_in_app":
                return self._open_in_app(action_json)
            elif action == "search_global":
                return self._search_global(action_json)
            elif action == "sys_info":
                return self._sys_info(action_json)
            elif action == "extract_text":
                return self._extract_text(action_json)
            elif action == "macro_record":
                return self._macro_record(action_json)
            elif action == "macro_play":
                return self._macro_play(action_json)
            elif action == "create_link":
                return self._create_link(action_json)
            elif action == "toggle_dark_mode":
                return self._toggle_dark_mode(action_json)
            elif action == "color_picker":
                return self._color_picker(action_json)
            elif action == "qr_scanner":
                return self._qr_scanner(action_json)
            elif action == "blur_snip":
                return self._blur_snip(action_json)
            elif action == "remove_bg":
                return self._remove_bg(action_json)
            elif action == "set_volume":
                return self._set_volume(action_json)
            elif action == "system_power":
                return self._system_power(action_json)
            elif action == "set_timer":
                return self._set_timer(action_json)
            elif action == "empty_trash":
                return self._empty_trash(action_json)
            elif action == "scratchpad":
                return self._scratchpad(action_json)
            elif action == "kill_app":
                return self._kill_app(action_json)
            elif action == "zip_files":
                return self._zip_files(action_json)
            elif action == "unzip_files":
                return self._unzip_files(action_json)
            elif action == "set_wallpaper":
                return self._set_wallpaper(action_json)
            elif action == "search_inside":
                return self._search_inside_files(action_json)
            elif action == "vault_read":
                return self._vault_read(action_json)
            elif action == "vault_cleanup":
                return self._vault_cleanup(action_json)
            else:
                return {"success": False, "message": f"Unknown action: {action}", "reverse_action": None}
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return {"success": False, "message": f"Exception: {str(e)}", "reverse_action": None}

    def _create_folder(self, data):
        folder_path = os.path.join(data.get("path", ""), data.get("name", "New Folder"))
        if os.path.exists(folder_path):
             return {"success": False, "message": "Folder already exists.", "reverse_action": None}
             
        os.makedirs(folder_path, exist_ok=True)
        
        # If created on the desktop and we have snip coordinates, position it
        snip_x = data.get("snip_x")
        snip_y = data.get("snip_y")
        if snip_x is not None and snip_y is not None:
            desktop_path = os.path.normpath(os.path.expanduser("~/Desktop"))
            if os.path.normpath(data.get("path", "")) == desktop_path:
                try:
                    import win32gui, commctrl
                    from pywinauto import Application
                    
                    # Find Desktop SysListView32
                    progman = win32gui.FindWindow("Progman", None)
                    shelldll = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
                    syslist = win32gui.FindWindowEx(shelldll, 0, "SysListView32", None)
                    if not syslist:
                        res = []
                        def enum_cb(hwnd, lparam):
                            shelldll = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                            if shelldll:
                                s = win32gui.FindWindowEx(shelldll, 0, "SysListView32", None)
                                if s: lparam.append(s)
                            return True
                        win32gui.EnumWindows(enum_cb, res)
                        if res: syslist = res[0]
                    
                    if syslist:
                        app = Application().connect(handle=syslist)
                        listview = app.window(handle=syslist).wrapper_object()
                        
                        # Wait briefly for Explorer to register the new folder
                        import time
                        time.sleep(0.5)
                        
                        item = listview.get_item(data.get("name", "New Folder"))
                        lparam = (int(snip_y) << 16) | (int(snip_x) & 0xFFFF)
                        win32gui.SendMessage(syslist, commctrl.LVM_SETITEMPOSITION, item.item_index, lparam)
                except Exception as e:
                    logger.error(f"Failed to position desktop icon: {e}")

        return {
            "success": True, 
            "message": f"Created folder {data.get('name')}",
            "reverse_action": {"action": "delete_folder", "path": folder_path}
        }

    def _create_file(self, data):
        file_path = os.path.join(data.get("path", ""), data.get("name", "new_file.txt"))
        if os.path.exists(file_path):
             return {"success": False, "message": "File already exists.", "reverse_action": None}
             
        with open(file_path, 'w') as f:
            pass # Create empty file
            
        return {
            "success": True, 
            "message": f"Created file {data.get('name')}",
            "reverse_action": {"action": "delete_file", "path": file_path}
        }

    def _delete_folder(self, data):
        path = os.path.join(data.get("path", ""), data.get("name", ""))
        if not path or not os.path.exists(path):
            return {"success": False, "message": "Folder not found.", "reverse_action": None}
        
        from send2trash import send2trash
        try:
            send2trash(path)
            # Give Windows a split second to process the move to recycle bin
            import time; time.sleep(0.5)
            
            return {
                "success": True,
                "message": f"Sent folder {data.get('name')} to Recycle Bin",
                "reverse_action": {"action": "restore_recycle_bin", "name": data.get("name"), "original_path": path}
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to recycle folder: {e}", "reverse_action": None}

    def _delete_file(self, data):
        path = os.path.join(data.get("path", ""), data.get("name", ""))
        if not os.path.exists(path):
            path = data.get("path", "")
        if not path or not os.path.exists(path):
            return {"success": False, "message": "File not found.", "reverse_action": None}
            
        from send2trash import send2trash
        try:
            send2trash(path)
            # Give Windows a split second to process
            import time; time.sleep(0.5)
            
            return {
                "success": True,
                "message": f"Sent file {os.path.basename(path)} to Recycle Bin",
                "reverse_action": {"action": "restore_recycle_bin", "name": os.path.basename(path), "original_path": path}
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to recycle file: {e}", "reverse_action": None}
            
    def _restore_recycle_bin(self, data):
        target_name = data.get("name")
        if not target_name:
            return {"success": False, "message": "Cannot undo: missing filename info.", "reverse_action": None}
            
        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            recycle_bin = shell.NameSpace(10) # CSIDL_BITBUCKET
            
            # Search items in Recycle Bin for our target
            restored = False
            for item in recycle_bin.Items():
                if item.Name == target_name:
                    # Execute the Restore verb
                    for verb in item.Verbs():
                        if "restore" in verb.Name.lower() or "undelete" in verb.Name.lower():
                            verb.DoIt()
                            restored = True
                            break
                    if restored:
                        break
                        
            if restored:
                return {
                    "success": True,
                    "message": f"Natively restored {target_name} from Windows Recycle Bin.",
                    "reverse_action": None
                }
            else:
                return {"success": False, "message": f"Could not find {target_name} in Recycle Bin.", "reverse_action": None}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to access Recycle Bin: {e}", "reverse_action": None}

    def _open_folder(self, data):
        path = data.get("path", "")
        name = data.get("name", "")
        if name:
            target_path = os.path.join(path, name)
            if os.path.exists(target_path):
                path = target_path
                
        if not path or not os.path.exists(path):
            return {"success": False, "message": "Path not found.", "reverse_action": None}
            
        os.startfile(path)
        return {
            "success": True,
            "message": f"Opened {path}",
            "reverse_action": None
        }

    def _convert_file(self, data):
        path = data.get("path", "")
        file_name = data.get("file_name", "")
        target_extension = data.get("target_extension", "").lower().strip('.')
        
        source_path = os.path.join(path, file_name)
        if not os.path.exists(source_path):
            return {"success": False, "message": "File not found for conversion.", "reverse_action": None}
            
        base_name = os.path.splitext(file_name)[0]
        output_name = f"{base_name}.{target_extension}"
        output_path = os.path.join(path, output_name)
        
        try:
            from PIL import Image
            with Image.open(source_path) as img:
                if target_extension in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(output_path)
            
            return {
                "success": True,
                "message": f"Converted {file_name} to .{target_extension}",
                "reverse_action": {"action": "delete_file", "path": path, "name": output_name}
            }
        except Exception as e:
            return {"success": False, "message": f"Conversion failed: {e}. Make sure it is an image file.", "reverse_action": None}

    def _move_file(self, data):
        src = data.get("from")
        dst = data.get("to")
        if not os.path.exists(src):
            return {"success": False, "message": "Source file not found.", "reverse_action": None}
            
        if not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)
            
        dst_path = os.path.join(dst, os.path.basename(src))
        shutil.move(src, dst_path)
        return {
            "success": True,
            "message": f"Moved to {dst}",
            "reverse_action": {"action": "move_file_back", "from": dst_path, "to": os.path.dirname(src)} 
        }

    def _rename_file(self, data):
        old_path = data.get("old_path")
        new_path = data.get("new_path")
        
        # Groq sometimes just gives the new name, not the full path
        if not os.path.isabs(new_path) and old_path:
            new_path = os.path.join(os.path.dirname(old_path), new_path)
            
        if not os.path.exists(old_path):
             return {"success": False, "message": "Original file not found.", "reverse_action": None}
             
        os.rename(old_path, new_path)
        return {
            "success": True,
            "message": "Renamed file successfully.",
            "reverse_action": {"action": "rename_file_back", "old_path": new_path, "new_path": old_path}
        }

    def _create_shortcut(self, data):
        target = data.get("target", "") 
        location = data.get("location", "")
        
        # If target isn't an absolute path, assume it's in the current location/context path
        if not os.path.isabs(target) and target:
            local_target = os.path.join(data.get("path", location), target)
            if os.path.exists(local_target):
                target = local_target
            elif self.search_api and target:
                results = []
                # If no extension was explicitly provided, they highly likely want the executable app
                if not os.path.splitext(target)[1]:
                    app_cmd = self._auto_find_app(target)
                    if app_cmd:
                        results = [app_cmd]
                    else:
                        results = self.search_api.search(f'"{target}.exe"')
                        if not results:
                            results = self.search_api.search(f"{target} ext:exe;lnk;url")
                    
                # If still no results, or an extension was provided, look for exact match
                if not results:
                    results = self.search_api.search(f'"{target}"')
                
                if results:
                    target = results[0] # Grab the first top result
                else: 
                    target = local_target # Fallback to broken local link
        
        shortcut_name = data.get("shortcut_name", "Shortcut")
        
        # If shortcut_name is an absolute path, extract just the base name so it's created in 'location'
        if os.path.isabs(shortcut_name) or ("\\" in shortcut_name) or ("/" in shortcut_name):
            shortcut_name = os.path.basename(shortcut_name)
            
        if not shortcut_name:
            shortcut_name = "Shortcut"
            
        if not shortcut_name.endswith(".lnk"):
            shortcut_name += ".lnk"
            
        shortcut_path = os.path.join(location, shortcut_name)
        
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            
            # Set WorkingDirectory so .cmd files and relative-path dependent apps work correctly
            if os.path.isabs(target):
                shortcut.WorkingDirectory = os.path.dirname(target)
                
            shortcut.save()
        except Exception as e:
            return {"success": False, "message": f"Failed to create shortcut: {e}", "reverse_action": None}
            
        return {
            "success": True,
            "message": "Shortcut created.",
            "reverse_action": {"action": "delete_shortcut", "path": shortcut_path}
        }

    def _arrange_by_type(self, data):
        path = data.get("path")
        if not os.path.exists(path):
            return {"success": False, "message": "Folder not found.", "reverse_action": None}
            
        reverse_moves = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item)[1].lower()
                category = "Others"
                for cat, exts in utils.FILE_CATEGORIES.items():
                    if ext in exts:
                        category = cat
                        break
                        
                dest_dir = os.path.join(path, category)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, item)
                
                shutil.move(item_path, dest_path)
                reverse_moves.append({"from": dest_path, "to": path})
                
        return {
            "success": True,
            "message": "Arranged files by type.",
            "reverse_action": {"action": "arrange_back", "moves": reverse_moves}
        }

    # ========== NEW FEATURES ==========

    def _copy_file(self, data):
        src = os.path.join(data.get("path", ""), data.get("name", ""))
        dst_folder = data.get("destination", "")
        
        if not os.path.exists(src):
            return {"success": False, "message": "Source not found.", "reverse_action": None}
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder, exist_ok=True)
            
        dst_path = os.path.join(dst_folder, os.path.basename(src))
        
        try:
            if os.path.isdir(src):
                if os.path.exists(dst_path):
                    shutil.copytree(src, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copytree(src, dst_path)
            else:
                # Auto-rename if file already exists
                if os.path.exists(dst_path):
                    base, ext = os.path.splitext(os.path.basename(src))
                    counter = 1
                    while os.path.exists(dst_path):
                        dst_path = os.path.join(dst_folder, f"{base}_copy{counter}{ext}")
                        counter += 1
                shutil.copy2(src, dst_path)
                
            return {
                "success": True,
                "message": f"Copied '{os.path.basename(src)}' to {dst_folder}",
                "reverse_action": {"action": "delete_file", "path": dst_folder, "name": os.path.basename(dst_path)}
            }
        except Exception as e:
            return {"success": False, "message": f"Copy failed: {e}", "reverse_action": None}

    def _duplicate_file(self, data):
        path = data.get("path", "")
        name = data.get("name", "")
        src = os.path.join(path, name)
        
        if not os.path.exists(src):
            return {"success": False, "message": "File not found.", "reverse_action": None}
            
        base, ext = os.path.splitext(name)
        copy_name = f"{base}_copy{ext}"
        counter = 1
        while os.path.exists(os.path.join(path, copy_name)):
            copy_name = f"{base}_copy{counter}{ext}"
            counter += 1
            
        dst = os.path.join(path, copy_name)
        
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
            
        return {
            "success": True,
            "message": f"Duplicated as {copy_name}",
            "reverse_action": {"action": "delete_file", "path": path, "name": copy_name}
        }

    def _file_info(self, data):
        path = data.get("path", "")
        name = data.get("name", "")
        target = os.path.join(path, name) if name else path
        
        if not os.path.exists(target):
            return {"success": False, "message": "File not found.", "reverse_action": None}
            
        stat = os.stat(target)
        size_bytes = stat.st_size
        
        # Human-readable size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            size_str = f"{size_bytes / (1024*1024):.1f} MB"
        else:
            size_str = f"{size_bytes / (1024*1024*1024):.2f} GB"
            
        created = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        file_type = "Folder" if os.path.isdir(target) else os.path.splitext(name)[1].upper() + " File"
        
        info = f"Name: {name} | Type: {file_type} | Size: {size_str} | Created: {created} | Modified: {modified}"
        
        return {"success": True, "message": info, "reverse_action": None}

    def _clean_empty(self, data):
        path = data.get("path", "")
        if not path or not os.path.exists(path):
            return {"success": False, "message": "Folder not found or no context folder active. Use this inside a specific folder view.", "reverse_action": None}
            
        removed = []
        # Walk bottom-up so nested empty folders get removed first
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            if dirpath == path:
                continue
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                removed.append(os.path.basename(dirpath))
                
        if removed:
            return {"success": True, "message": f"Removed {len(removed)} empty folders: {', '.join(removed)}", "reverse_action": None}
        else:
            return {"success": True, "message": "No empty folders found.", "reverse_action": None}

    def _flatten_folder(self, data):
        path = data.get("path", "")
        if not os.path.exists(path):
            return {"success": False, "message": "Folder not found.", "reverse_action": None}
            
        reverse_moves = []
        moved_count = 0
        
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            if dirpath == path:
                continue
            for fname in filenames:
                src = os.path.join(dirpath, fname)
                dst = os.path.join(path, fname)
                
                # Handle name collisions
                if os.path.exists(dst):
                    base, ext = os.path.splitext(fname)
                    counter = 1
                    while os.path.exists(dst):
                        dst = os.path.join(path, f"{base}_{counter}{ext}")
                        counter += 1
                        
                shutil.move(src, dst)
                reverse_moves.append({"from": dst, "to": dirpath})
                moved_count += 1
                
        # Remove now-empty subdirectories
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            if dirpath == path:
                continue
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                
        return {
            "success": True,
            "message": f"Flattened folder. Moved {moved_count} files to top level.",
            "reverse_action": {"action": "arrange_back", "moves": reverse_moves}
        }

    def _bulk_rename(self, data):
        path = data.get("path", "")
        prefix = data.get("prefix", "")
        suffix = data.get("suffix", "")
        numbering = data.get("numbering", False)
        file_filter = data.get("filter", "")  # e.g. ".txt", ".jpg"
        
        if not os.path.exists(path):
            return {"success": False, "message": "Folder not found.", "reverse_action": None}
            
        reverse_renames = []
        counter = 1
        
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if not os.path.isfile(item_path):
                continue
                
            base, ext = os.path.splitext(item)
            
            # If filter is set, only rename matching extensions
            if file_filter and ext.lower() != file_filter.lower():
                continue
                
            if numbering:
                new_name = f"{prefix}{counter:03d}{suffix}{ext}"
                counter += 1
            else:
                new_name = f"{prefix}{base}{suffix}{ext}"
                
            new_path = os.path.join(path, new_name)
            if new_path != item_path:
                os.rename(item_path, new_path)
                reverse_renames.append({"old_path": new_path, "new_path": item_path})
                
        if reverse_renames:
            return {
                "success": True,
                "message": f"Renamed {len(reverse_renames)} files.",
                "reverse_action": {"action": "bulk_rename_back", "renames": reverse_renames}
            }
        else:
            return {"success": True, "message": "No matching files to rename.", "reverse_action": None}

    def _find_duplicates(self, data):
        path = data.get("path", "")
        if not os.path.exists(path):
            return {"success": False, "message": "Folder not found.", "reverse_action": None}
            
        # Group files by size first (fast filter)
        size_map = {}
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                size_map.setdefault(size, []).append(item)
                
        # For groups with same size, compare hashes
        duplicates = []
        for size, files in size_map.items():
            if len(files) < 2:
                continue
            hash_map = {}
            for fname in files:
                fpath = os.path.join(path, fname)
                file_hash = self._hash_file(fpath)
                hash_map.setdefault(file_hash, []).append(fname)
                
            for h, group in hash_map.items():
                if len(group) > 1:
                    duplicates.append(group)
                    
        if duplicates:
            msg_parts = []
            for group in duplicates:
                msg_parts.append(" = ".join(group))
            return {"success": True, "message": f"Found {len(duplicates)} duplicate set(s): {' | '.join(msg_parts)}", "reverse_action": None}
        else:
            return {"success": True, "message": "No duplicate files found.", "reverse_action": None}

    def _hash_file(self, filepath, block_size=65536):
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()

    def _disk_usage(self, data):
        path = data.get("path", "")
        if not os.path.exists(path):
            return {"success": False, "message": "Folder not found.", "reverse_action": None}
            
        total_size = 0
        type_sizes = {}
        file_count = 0
        folder_count = 0
        
        for dirpath, dirnames, filenames in os.walk(path):
            folder_count += len(dirnames)
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                try:
                    size = os.path.getsize(fpath)
                    total_size += size
                    file_count += 1
                    ext = os.path.splitext(fname)[1].lower() or "(no ext)"
                    type_sizes[ext] = type_sizes.get(ext, 0) + size
                except:
                    pass
                    
        # Human-readable total
        if total_size < 1024:
            total_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            total_str = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            total_str = f"{total_size / (1024*1024):.1f} MB"
        else:
            total_str = f"{total_size / (1024*1024*1024):.2f} GB"
            
        # Top 5 extensions by size
        sorted_types = sorted(type_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
        breakdown = ", ".join([f"{ext}: {s/(1024*1024):.1f}MB" if s > 1024*1024 else f"{ext}: {s/1024:.1f}KB" for ext, s in sorted_types])
        
        msg = f"Total: {total_str} | {file_count} files, {folder_count} folders | Top types: {breakdown}"
        return {"success": True, "message": msg, "reverse_action": None}

    # ========== TAG FEATURES ==========

    def _add_tag(self, data):
        path = data.get("path", "")
        name = data.get("name", "")
        tag = data.get("tag", "")
        
        target = os.path.join(path, name) if name else path
        if not os.path.exists(target):
            return {"success": False, "message": "File not found.", "reverse_action": None}
        if not tag:
            return {"success": False, "message": "No tag specified.", "reverse_action": None}
            
        added = self.tag_manager.add_tag(target, tag)
        if added:
            return {
                "success": True,
                "message": f"Tagged '{name or os.path.basename(path)}' with [{tag}].",
                "reverse_action": {"action": "remove_tag", "path": path, "name": name, "tag": tag}
            }
        else:
            return {"success": True, "message": f"File already has the tag [{tag}].", "reverse_action": None}

    def _remove_tag(self, data):
        path = data.get("path", "")
        name = data.get("name", "")
        tag = data.get("tag", "")
        
        target = os.path.join(path, name) if name else path
        removed = self.tag_manager.remove_tag(target, tag)
        if removed:
            return {"success": True, "message": f"Removed tag [{tag}] from '{name or os.path.basename(path)}'.", "reverse_action": None}
        else:
            return {"success": False, "message": "Tag not found on this file.", "reverse_action": None}

    def _search_by_tag(self, data):
        tag = data.get("tag", "")
        folder = data.get("path", "")
        
        if not tag:
            return {"success": False, "message": "No tag specified.", "reverse_action": None}
            
        results = self.tag_manager.search_by_tag(tag, folder if folder else None)
        if results:
            file_list = ", ".join([os.path.basename(r) for r in results])
            return {"success": True, "message": f"Files tagged [{tag}]: {file_list}", "reverse_action": None}
        else:
            return {"success": True, "message": f"No files found with tag [{tag}].", "reverse_action": None}

    def _list_tags(self, data):
        folder = data.get("path", "")
        # Group by tags
        collections = {}
        for filepath, tags in self.tag_manager.tags.items():
            if folder:
                if not filepath.startswith(os.path.normpath(folder)):
                    continue
            if os.path.exists(filepath):
                for t in tags:
                    collections.setdefault(t, []).append(filepath)
        
        if not collections:
            return {"success": True, "message": "No tagged files found.", "reverse_action": None}
            
        html_msg = "<b>&#127991; Tag Collections:</b><br><br>"
        for t, paths in collections.items():
            html_msg += f"<span style='color: #FF7F50; font-weight: bold;'>#{t}</span><br>"
            for p in paths:
                fname = os.path.basename(p)
                p_uri = p.replace('\\', '/')
                html_msg += f"&nbsp;&nbsp;&bull; <a href='file:///{p_uri}' style='color: #88c0d0; text-decoration: none;'>{fname}</a><br>"
            html_msg += "<br>"
            
        return {"success": True, "message": html_msg, "reverse_action": None}

    def _open_in_app(self, data):
        import subprocess
        from settings_manager import SettingsManager
        
        app_name = data.get("app_name", "")
        target_path = data.get("target", "")
        
        # Build full target path only if an explicit target was given
        if target_path and target_path.lower() not in ["", "null", "none"]:
            if not os.path.isabs(target_path):
                ctx_path = data.get("path", "")
                target_path = os.path.join(ctx_path, target_path)
        else:
            target_path = ""
        
        settings = SettingsManager()
        app_cmd = settings.get_app_command(app_name)
        
        # If not registered, try to auto-find using Everything or PowerShell
        if not app_cmd:
            app_cmd = self._auto_find_app(app_name)
            if app_cmd:
                apps = settings.get("applications", {})
                apps[app_name.lower()] = app_cmd
                settings.set("applications", apps)
        
        if not app_cmd:
            # Final fallback: let Windows try to open it (handles PATH, protocols, and UWP apps)
            try:
                os.startfile(app_name)
                return {"success": True, "message": f"Launched '{app_name}' via system default.", "reverse_action": None}
            except Exception:
                # Extra fallback: If Windows startfile fails, search Everything and open the best match directly
                if self.search_api:
                    try:
                        results = self.search_api.search(app_name, limit=5)
                        if results:
                            # Try to find an exact match, otherwise take the first one
                            best_match = results[0]
                            for r in results:
                                if os.path.basename(r).lower() == app_name.lower() or os.path.basename(r).lower().startswith(app_name.lower()):
                                    best_match = r
                                    break
                            os.startfile(best_match)
                            return {"success": True, "message": f"Launched '{os.path.basename(best_match)}' via system search.", "reverse_action": None}
                    except Exception:
                        pass
                
                available = ", ".join(settings.get_app_names()) if settings.get_app_names() else "none"
                return {"success": False, "message": f"App '{app_name}' not found. Available: {available}. Add it in Settings.", "reverse_action": None}
        
        try:
            app_dir = os.path.dirname(app_cmd)
            if target_path:
                full_command = f'"{app_cmd}" "{target_path}"'
                msg = f"Opened '{os.path.basename(target_path)}' in {app_name}"
            else:
                full_command = f'"{app_cmd}"'
                msg = f"Launched {app_name}"
                
            # Set cwd to the app's directory so games/apps with relative dependencies launch correctly
            subprocess.Popen(full_command, shell=True, cwd=app_dir if app_dir else None)
            return {"success": True, "message": msg, "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Failed to open {app_name}: {e}", "reverse_action": None}
    
    def _auto_find_app(self, app_name):
        """Use Everything to find an app executable by name."""
        # Common aliases for apps whose exe name differs from display name
        aliases = {
            'edge': 'msedge',
            'microsoft edge': 'msedge',
            'vs code': 'Code',
            'visual studio code': 'Code',
            'word': 'WINWORD',
            'excel': 'EXCEL',
            'powerpoint': 'POWERPNT',
            'firefox': 'firefox',
            'brave': 'brave',
            'vlc': 'vlc',
            'spotify': 'Spotify',
            'steam': 'steam',
            'discord': 'Discord',
            'telegram': 'Telegram',
            'obs': 'obs64',
            'gta v': 'PlayGTAV',
            'tlauncher': 'tlauncher'
        }
        
        search_name = aliases.get(app_name.lower(), app_name)
        search_normalized = search_name.replace(" ", "").lower()
        
        found_path = None
        
        if self.search_api:
            try:
                searches = [
                    f'{search_name}.exe',
                    f'{search_name}64.exe',
                    f'{app_name}.exe',
                    f'{app_name} ext:exe',
                ]
                
                for query in searches:
                    results = self.search_api.search(query, limit=15)
                    for r in results:
                        r_lower = r.lower()
                        basename = os.path.basename(r_lower)
                        
                        if any(skip in r_lower for skip in ['unins', 'update', 'crash', 'setup', 'helper', 'temp', 'cache', 'old', 'backup', 'system32']):
                            continue
                        if not r_lower.endswith('.exe'):
                            continue
                            
                        # Strict check: the basename MUST contain the search term
                        if search_normalized in basename.replace("-", "").replace("_", ""):
                            found_path = r
                            break
                    if found_path:
                        break
            except Exception:
                pass
                
        if found_path:
            return found_path
            
        # Fallback: Search Start Menu shortcuts and App Paths registry using PowerShell
        try:
            import subprocess
            ps_script = f"""
            $app = "{search_name}"
            $paths = @(
                "$env:ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
                "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs",
                "$env:USERPROFILE\\Desktop",
                "$env:PUBLIC\\Desktop"
            )
            $shortcut = Get-ChildItem -Path $paths -Recurse -Include "*$app*.lnk" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($shortcut) {{
                $shell = New-Object -ComObject WScript.Shell
                Write-Output $shell.CreateShortcut($shortcut.FullName).TargetPath
            }} else {{
                $regPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths"
                $regApp = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue | Where-Object {{ $_.PSChildName -match "$app" }} | Select-Object -First 1
                if ($regApp) {{
                    $val = Get-ItemProperty -Path $regApp.PSPath -Name "(default)" -ErrorAction SilentlyContinue
                    if ($val) {{
                        Write-Output $val."(default)"
                    }}
                }}
            }}
            """
            result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, timeout=5)
            ps_path = result.stdout.strip()
            if ps_path and os.path.exists(ps_path):
                return ps_path
        except Exception as e:
            logger.error(f"PowerShell app search failed: {e}")
            
        return None

    def _search_global(self, data):
        """Search for files/folders globally using Everything API."""
        query = data.get("query", "")
        should_open = data.get("open", False)
        
        if not query:
            return {"success": False, "message": "No search query provided.", "reverse_action": None}
            
        common_folders = ["downloads", "desktop", "documents", "pictures", "videos", "music"]
        if query.lower() in common_folders:
            user_profile = os.environ.get("USERPROFILE", "")
            target = os.path.join(user_profile, query.capitalize())
            if os.path.exists(target):
                if should_open:
                    os.startfile(target)
                clean_path = target.replace('\\', '/')
                html = f"Located your OS folder:<br><br>1. <a href='file:///{clean_path}' style='color:#88c0d0;'>{target}</a>"
                return {"success": True, "message": html, "reverse_action": None}
        
        if not self.search_api:
            return {"success": False, "message": "Everything search is not available. Make sure Everything is running.", "reverse_action": None}
        
        try:
            results = self.search_api.search(query, limit=8)
            
            if not results:
                return {"success": True, "message": f"No results found for '{query}'.", "reverse_action": None}
            
            if should_open and results:
                target = results[0]
                if os.path.isdir(target):
                    os.startfile(target)
                elif os.path.isfile(target):
                    os.startfile(target)
                return {"success": True, "message": f"Opened: {target}", "reverse_action": None}
            
            # Format results as clickable file URIs
            result_lines = []
            for i, r in enumerate(results, 1):
                # Ensure the path works natively with Windows file:// schema by replacing spaces/slashes if needed,
                # though PyQt QUrl usually parses standard windows paths cleanly inside an href if prefaced with file:///
                clean_path = r.replace('\\', '/')
                result_lines.append(f"{i}. <a href='file:///{clean_path}' style='color:#88c0d0;'>{r}</a>")
            
            result_text = f"Found {len(results)} results for '{query}':<br>" + "<br>".join(result_lines)
            return {"success": True, "message": result_text, "reverse_action": None}
            
        except Exception as e:
            return {"success": False, "message": f"Search failed: {e}", "reverse_action": None}

    def _sys_info(self, data):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            try:
                battery = psutil.sensors_battery()
                batt_str = f"| Battery: {battery.percent}%" if battery else ""
            except:
                batt_str = ""
            msg = f"CPU: {cpu}% | RAM: {ram.percent}% ({ram.used/(1024**3):.1f}GB/{ram.total/(1024**3):.1f}GB) {batt_str}"
            return {"success": True, "message": msg, "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Could not fetch sysinfo. Run 'pip install psutil'.", "reverse_action": None}

    def _extract_text(self, data):
        image = data.get("image")
        if not image:
            return {"success": False, "message": "No image snip available to extract from. Use Ctrl+Shift+S first.", "reverse_action": None}
        try:
            import pytesseract
            import pyperclip
            text = pytesseract.image_to_string(image).strip()
            if not text:
                return {"success": True, "message": "No text detected in the image.", "reverse_action": None}
            pyperclip.copy(text)
            return {"success": True, "message": f"Extracted text copied to clipboard:\n\n{text}", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"OCR failed. Please ensure 'pytesseract' is installed and configured.", "reverse_action": None}

    def _macro_record(self, data):
        """Record mouse + keyboard events to a JSON file using pynput."""
        name = data.get("name", "last_macro")
        done_cb = data.get("_done_cb")  # Optional callback to notify chat
        macro_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macros")
        os.makedirs(macro_dir, exist_ok=True)
        macro_file = os.path.join(macro_dir, f"{name}.json")
        try:
            from pynput import mouse as _mouse, keyboard as _kb
            import threading, json, time
            events = []
            start = time.time()
            recording = [True]

            def on_move(x, y):
                if recording[0]:
                    events.append({"t": round(time.time()-start,3), "type": "move", "x": x, "y": y})
            def on_click(x, y, btn, pressed):
                if recording[0]:
                    events.append({"t": round(time.time()-start,3), "type": "click",
                                   "x": x, "y": y, "btn": str(btn), "pressed": pressed})
            def on_press(key):
                k = key.char if hasattr(key, 'char') and key.char else str(key)
                if k == 'Key.esc':
                    recording[0] = False
                    return False
                if recording[0]:
                    events.append({"t": round(time.time()-start,3), "type": "kp", "k": k})
            def on_release(key):
                k = key.char if hasattr(key, 'char') and key.char else str(key)
                if recording[0]:
                    events.append({"t": round(time.time()-start,3), "type": "kr", "k": k})

            def _run():
                with _mouse.Listener(on_move=on_move, on_click=on_click) as ml, \
                     _kb.Listener(on_press=on_press, on_release=on_release) as kl:
                    kl.join()
                with open(macro_file, 'w') as f:
                    json.dump(events, f)
                logger.info(f"Macro '{name}' saved with {len(events)} events.")
                # Notify the chat popup that recording is done
                if done_cb:
                    try:
                        done_cb(name)
                    except Exception:
                        pass

            threading.Thread(target=_run, daemon=True).start()
            return {"success": True,
                    "message": f"Recording macro <b>'{name}'</b>... Press <b>Esc</b> to stop.",
                    "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Macro record failed: {e}. Ensure 'pynput' is installed.", "reverse_action": None}


    def _macro_play(self, data):
        """Replay a recorded macro JSON file using pynput controllers."""
        name = data.get("name", "last_macro")
        macro_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macros")
        macro_file = os.path.join(macro_dir, f"{name}.json")
        if not os.path.exists(macro_file):
            available = [f.replace('.json','') for f in os.listdir(macro_dir)] \
                        if os.path.exists(macro_dir) else []
            return {"success": False,
                    "message": f"Macro '{name}' not found. Available: {', '.join(available) or 'none'}",
                    "reverse_action": None}
        try:
            from pynput.mouse import Button, Controller as MC
            from pynput.keyboard import Key, Controller as KC
            import threading, json, time
            with open(macro_file) as f:
                events = json.load(f)

            def _play():
                mc, kc = MC(), KC()
                prev = 0.0
                for ev in events:
                    delay = ev["t"] - prev
                    if delay > 0:
                        time.sleep(min(delay, 1.5))
                    prev = ev["t"]
                    try:
                        tp = ev["type"]
                        if tp == "move":
                            mc.position = (ev["x"], ev["y"])
                        elif tp == "click":
                            btn = Button.left if "left" in ev["btn"] else Button.right
                            (mc.press if ev["pressed"] else mc.release)(btn)
                        elif tp in ("kp", "kr"):
                            k = ev["k"]
                            key_obj = getattr(Key, k[4:], None) if k.startswith("Key.") else k
                            (kc.press if tp == "kp" else kc.release)(key_obj)
                    except Exception:
                        pass
            threading.Thread(target=_play, daemon=True).start()
            return {"success": True,
                    "message": f"\u25b6\ufe0f Playing macro <b>'{name}'</b> ({len(events)} events)\u2026",
                    "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Macro play failed: {e}", "reverse_action": None}

    def _create_link(self, data):
        """Upload the current snip to 0x0.st and return a real shareable URL."""
        image = data.get("image")
        if not image:
            return {"success": False, "message": "No snip to upload. Take a screenshot first.", "reverse_action": None}
        try:
            import requests, tempfile, os
            from io import BytesIO
            # Save PIL image to a temp PNG
            buf = BytesIO()
            image.save(buf, format="PNG")
            buf.seek(0)
            response = requests.post(
                "https://0x0.st",
                files={"file": ("coral_snip.png", buf, "image/png")},
                timeout=15
            )
            if response.status_code == 200:
                url = response.text.strip()
                # Copy to clipboard
                try:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.clipboard().setText(url)
                    clipboard_note = " (copied to clipboard)"
                except Exception:
                    clipboard_note = ""
                return {
                    "success": True,
                    "message": f"Snip uploaded! Link: <a href='{url}' style='color:#88c0d0;'>{url}</a>{clipboard_note}",
                    "reverse_action": None
                }
            else:
                return {"success": False, "message": f"Upload failed: server returned {response.status_code}.", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Upload failed: {e}", "reverse_action": None}

    def _toggle_dark_mode(self, data):
        import ctypes
        import winreg
        try:
            # Toggle Windows dark mode registry
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(hkey, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)
            return {"success": True, "message": "Set Windows to Dark Mode.", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Failed to toggle dark mode: {e}", "reverse_action": None}

    def _color_picker(self, data):
        image = data.get("image")
        if not image:
            return {"success": False, "message": "No image snip available. Use Ctrl+Shift+S first.", "reverse_action": None}
        
        try:
            from PIL import Image
            import pyperclip
            
            # Resize and reduce colors for dominant color extraction
            img = image.copy().convert('RGB')
            img.thumbnail((100, 100))
            quantized = img.quantize(colors=5).convert('RGB')
            
            # Get the top colors from the quantized image
            colors = quantized.getcolors(100*100)
            if not colors:
                 return {"success": False, "message": "Could not extract colors.", "reverse_action": None}
                 
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
            
            top_colors = []
            for count, color in sorted_colors:
                hex_val = '#{:02x}{:02x}{:02x}'.format(*color)
                top_colors.append(f"{hex_val} (RGB: {color})")
            
            if top_colors:
                pyperclip.copy(top_colors[0].split()[0])
            
            msg = "<b>Dominant Colors extracted:</b><br>" + "<br>".join([f"<span style='color:{c.split()[0]}'>■</span> {c}" for c in top_colors])
            msg += "<br><br><i>Most dominant hex copied to clipboard!</i>"
            
            return {"success": True, "message": msg, "reverse_action": None}
        except Exception as e:
            logger.error(f"Color extraction failed: {e}")
            return {"success": False, "message": f"Color extraction failed: {e}", "reverse_action": None}

    def _qr_scanner(self, data):
        image = data.get("image")
        if not image:
            return {"success": False, "message": "No image snip available. Use Ctrl+Shift+S first.", "reverse_action": None}
        
        try:
            from pyzbar.pyzbar import decode
            import pyperclip
            import webbrowser
            
            # pyzbar likes PIL images or numpy arrays
            results = decode(image)
            
            if not results:
                return {"success": True, "message": "No QR codes or Barcodes detected in this region.", "reverse_action": None}
            
            from settings_manager import SettingsManager
            settings = SettingsManager()
            auto_open = settings.get("qr_open_browser", False)
            auto_copy = settings.get("qr_copy_clipboard", False)

            found = []
            for obj in results:
                data_str = obj.data.decode('utf-8')
                type_str = obj.type
                # Format as clickable inline link
                if data_str.startswith(('http://', 'https://')):
                    html_entry = f"[{type_str}] <a href='{data_str}' style='color:#88c0d0;'>{data_str}</a>"
                    found.append(html_entry)
                else:
                    found.append(f"[{type_str}] {data_str}")
                
            # Take the first one for auto-action
            first_data = results[0].data.decode('utf-8')
            msg_extras = []
            
            if auto_copy:
                pyperclip.copy(first_data)
                msg_extras.append("Copied to clipboard.")
            
            if first_data.startswith(('http://', 'https://')) and auto_open:
                webbrowser.open(first_data)
                msg_extras.append("Opened in browser.")
                
            msg = f"<b>Detected {len(found)} code(s):</b><br>" + "<br>".join(found)
            if msg_extras:
                msg += "<br><br><i>" + " ".join(msg_extras) + "</i>"
                
            return {"success": True, "message": msg, "reverse_action": None}
        except Exception as e:
            logger.error(f"QR Scanning failed: {e}")
            return {"success": False, "message": f"Scanner failed: {e}. If on Windows, ensure C++ Redistributable is installed and 'pyzbar' is installed correctly.", "reverse_action": None}

    def _blur_snip(self, data):
        image = data.get("image")
        if not image:
            return {"success": False, "message": "No image snip available.", "reverse_action": None}
        
        try:
            from PIL import ImageFilter
            blurred = image.filter(ImageFilter.GaussianBlur(radius=10))
            # Return the blurred image so the UI can update
            return {"success": True, "message": "Snip blurred successfully.", "new_image": blurred, "reverse_action": None}
        except Exception as e:
            logger.error(f"Blur failed: {e}")
            return {"success": False, "message": f"Blur failed: {e}", "reverse_action": None}

    def _remove_bg(self, data):
        image = data.get("image")
        if not image:
            return {"success": False, "message": "No image snip available.", "reverse_action": None}
        
        try:
            from rembg import remove
            result_img = remove(image)
            return {"success": True, "message": "Background removed successfully. Preview updated.", "new_image": result_img, "reverse_action": None}
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return {"success": False, "message": f"Background removal failed: {e}. Ensure 'rembg' is installed.", "reverse_action": None}

    def _set_volume(self, data):
        level = data.get("level", 50)  # 0-100
        mute = data.get("mute", False)
        
        try:
            from pycaw.pycaw import AudioUtilities
            device = AudioUtilities.GetSpeakers()
            volume = device.EndpointVolume  # correct API for newer pycaw
            
            if mute:
                volume.SetMute(1, None)
                return {"success": True, "message": "&#128263; System muted.", "reverse_action": {"action": "set_volume", "level": int(volume.GetMasterVolumeLevelScalar() * 100), "mute": False}}
            else:
                volume.SetMute(0, None)
                volume.SetMasterVolumeLevelScalar(float(level) / 100.0, None)
                return {"success": True, "message": f"&#128266; Volume set to {level}%.", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Volume control failed: {e}", "reverse_action": None}

    def _system_power(self, data):
        mode = data.get("mode", "lock") # lock, sleep, hibernate
        try:
            import ctypes
            if mode == "lock":
                ctypes.windll.user32.LockWorkStation()
                return {"success": True, "message": "Workstation locked.", "reverse_action": None}
            elif mode == "sleep":
                # 0, 1, 0 = Sleep
                ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
                return {"success": True, "message": "Putting PC to sleep...", "reverse_action": None}
            elif mode == "hibernate":
                ctypes.windll.PowrProf.SetSuspendState(1, 1, 0)
                return {"success": True, "message": "PC Hibernating...", "reverse_action": None}
            return {"success": False, "message": f"Unknown power mode: {mode}", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Power command failed: {e}", "reverse_action": None}

    def _set_timer(self, data):
        """Real background timer using threading.Timer — fires a Windows popup on completion."""
        seconds = data.get("seconds", 60)
        label = data.get("label", "Timer")
        try:
            import threading, ctypes
            def _fire():
                ctypes.windll.user32.MessageBoxW(
                    0, f"\u23f0 Timer '{label}' is done!", "Coral Timer", 0x40)
            t = threading.Timer(float(seconds), _fire)
            t.daemon = True
            t.start()
            mins, secs = divmod(int(seconds), 60)
            h, m2 = divmod(mins, 60)
            time_str = (f"{h}h {m2}m {secs}s" if h else
                        f"{m2}m {secs}s" if m2 else f"{secs}s")
            return {"success": True,
                    "message": f"\u23f0 Timer set for <b>{time_str}</b> (‘{label}’). A popup will appear when done.",
                    "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Timer failed: {e}", "reverse_action": None}

    def _empty_trash(self, data):
        try:
            import ctypes
            # SHEmptyRecycleBinW(HWND, RootPath, Flags)
            # Flags: 1 = SHERB_NOCONFIRMATION, 2 = SHERB_NOPROGRESSUI, 4 = SHERB_NOSOUND
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
            return {"success": True, "message": "Recycle Bin emptied.", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Failed to empty trash: {e}", "reverse_action": None}

    def _scratchpad(self, data):
        text = data.get("text", "")
        if not text:
            return {"success": False, "message": "No text provided to save.", "reverse_action": None}
        
        try:
            sp_path = os.path.join(os.path.dirname(__file__), "coral_scratchpad.txt")
            with open(sp_path, "a", encoding="utf-8") as f:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                f.write(f"[{ts}]\n{text}\n\n")
            sp_uri = sp_path.replace("\\", "/")
            return {
                "success": True,
                "message": f"&#128203; Saved to vault. <a href='file:///{sp_uri}' style='color:#88c0d0;'>Open scratchpad</a>",
                "reverse_action": None
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to save to scratchpad: {e}", "reverse_action": None}

    def _zip_files(self, data):
        name = data.get("name")
        path = data.get("path")
        target = os.path.join(path, name) if path else name
        
        if not os.path.exists(target):
            # Fallback to Everything Search if not in current context/global mode
            if self.search_api:
                results = self.search_api.search(f'"{name}"')
                if results:
                    target = results[0]
                    path = os.path.dirname(target)
            
        if not os.path.exists(target):
            return {"success": False, "message": f"Target '{name}' not found.", "reverse_action": None}
            
        import zipfile
        zip_path = target + ".zip"
        
        try:
            if os.path.isdir(target):
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(target):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(target))
                            zipf.write(file_path, arcname)
            else:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(target, os.path.basename(target))
                    
            return {
                "success": True, 
                "message": f"Successfully zipped '{name}'", 
                "reverse_action": {"action": "delete_file", "name": name + ".zip", "path": path}
            }
        except Exception as e:
            return {"success": False, "message": f"Zip failed: {e}", "reverse_action": None}

    def _unzip_files(self, data):
        name = data.get("name")
        path = data.get("path")
        
        if not name.endswith(".zip"):
            name += ".zip"
            
        target = os.path.join(path, name) if path else name
        
        if not os.path.exists(target):
            # Fallback to Everything Search if not in current context/global mode
            if self.search_api:
                results = self.search_api.search(f'"{name}"')
                if results:
                    target = results[0]
                    # Update 'path' to the newly found item's parent directory so extraction happens there
                    path = os.path.dirname(target)
            
        if not os.path.exists(target):
            return {"success": False, "message": f"Zip file '{name}' not found.", "reverse_action": None}
            
        import zipfile
        base_name = os.path.basename(name)
        extract_folder = os.path.join(path, base_name[:-4])
        
        try:
            with zipfile.ZipFile(target, 'r') as zipf:
                zipf.extractall(extract_folder)
            return {
                "success": True, 
                "message": f"Successfully extracted to '{name[:-4]}'", 
                "reverse_action": {"action": "delete_folder", "name": name[:-4], "path": path}
            }
        except Exception as e:
            return {"success": False, "message": f"Unzip failed: {e}", "reverse_action": None}

    def _vault_read(self, data):
        n = int(data.get("n", 5))
        try:
            sp_path = os.path.join(os.path.dirname(__file__), "coral_scratchpad.txt")
            if not os.path.exists(sp_path):
                return {"success": True, "message": "Vault is currently empty.", "reverse_action": None}
            with open(sp_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return {"success": True, "message": "Vault is currently empty.", "reverse_action": None}
            
            entries = [e for e in content.split("\n\n") if e.strip()]
            recent = entries[-n:] if n > 0 else entries
            recent.reverse()  # newest first
            
            sp_uri = sp_path.replace("\\", "/")
            html = f"<b>&#128203; Vault — last {len(recent)} entries:</b> <a href='file:///{sp_uri}' style='color:#88c0d0; font-size:11px;'>[open file]</a><br><br>"
            for entry in recent:
                lines = entry.strip().splitlines()
                if lines and lines[0].startswith("["):
                    ts = lines[0]
                    body = "<br>".join(lines[1:])
                else:
                    ts = ""
                    body = "<br>".join(lines)
                html += f"<span style='color:#888; font-size:10px;'>{ts}</span><br>"
                html += f"<span style='color:#eee;'>{body}</span><br><br>"
            
            return {"success": True, "message": html, "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Failed to read vault: {e}", "reverse_action": None}

    def _vault_cleanup(self, data):
        days = data.get("days", 7)
        try:
            if not os.path.exists("coral_scratchpad.txt"):
                return {"success": True, "message": "Vault is empty, nothing to clean.", "reverse_action": None}
                
            with open("coral_scratchpad.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            if not content:
                return {"success": True, "message": "Vault is empty, nothing to clean.", "reverse_action": None}
                
            entries = [e for e in content.split("\n\n") if e.strip()]
            new_entries = []
            
            cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
            removed_count = 0
            
            for entry in entries:
                if entry.startswith("["):
                    end_idx = entry.find("]")
                    if end_idx != -1:
                        ts_str = entry[1:end_idx]
                        try:
                            # Format is "%Y-%m-%d %H:%M"
                            entry_date = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
                            if entry_date > cutoff:
                                new_entries.append(entry)
                            else:
                                removed_count += 1
                        except:
                            new_entries.append(entry) # Keep if parsing fails
                    else:
                        new_entries.append(entry)
                else:
                    new_entries.append(entry)
                    
            if removed_count > 0:
                with open("coral_scratchpad.txt", "w", encoding="utf-8") as f:
                    if new_entries:
                        f.write("\n\n".join(new_entries) + "\n\n")
                    else:
                        f.write("")
                return {"success": True, "message": f"Cleaned up {removed_count} entries older than {days} days.", "reverse_action": None}
            else:
                return {"success": True, "message": "Vault is already clean.", "reverse_action": None}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to clean up vault: {e}", "reverse_action": None}
    def _kill_app(self, data):
        app_name = (data.get("app") or data.get("name") or "").replace(".exe", "")
        if not app_name:
            return {"success": False, "message": "Specify an app to kill.", "reverse_action": None}
        try:
            import subprocess
            subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"], capture_output=True)
            return {"success": True, "message": f"&#127937; {app_name}.exe has been successfully terminated.", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Failed to kill: {e}", "reverse_action": None}

    def _toggle_dark_mode(self, data):
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                new_val = 1 if value == 0 else 0
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new_val)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_val)
            
            mode = "Light" if new_val == 1 else "Dark"
            return {"success": True, "message": f"&#127769; Switched to {mode} mode.", "reverse_action": {"action": "toggle_dark_mode"}}
        except Exception as e:
            return {"success": False, "message": f"Failed to toggle theme: {e}", "reverse_action": None}

    def _sys_info(self, data):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            batt = psutil.sensors_battery()
            batt_str = f"{batt.percent}%" if batt else "N/A"
            
            html = f"<b>&#128187; System Diagnostics:</b><br>"
            html += f"&bull; CPU Usage: <b>{cpu}%</b><br>"
            html += f"&bull; RAM Usage: <b>{ram}%</b><br>"
            html += f"&bull; Battery: <b>{batt_str}</b>"
            return {"success": True, "message": html, "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"SysInfo failed: {e}", "reverse_action": None}

    def _set_wallpaper(self, data):
        img = data.get("image")
        if not img:
            return {"success": False, "message": "No image to set as wallpaper.", "reverse_action": None}
        try:
            import ctypes
            # Save to temp file
            temp_path = os.path.join(os.environ["TEMP"], "coral_wallpaper.jpg")
            img.convert("RGB").save(temp_path, "JPEG")
            # SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_path, 3)
            return {"success": True, "message": "&#128444; Desktop wallpaper updated!", "reverse_action": None}
        except Exception as e:
            return {"success": False, "message": f"Wallpaper failed: {e}", "reverse_action": None}


