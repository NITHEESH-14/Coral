import sys
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, QObject, Q_ARG, pyqtSlot
import pystray
from PIL import Image, ImageDraw
import utils
from overlay import SelectionOverlay
from context import capture_context, _get_folder_items
import os
from popup import ChatPopup

logger = utils.setup_logger(__name__)

class AIWorker(QThread):
    finished = pyqtSignal(str, object)
    
    def __init__(self, client, context, text):
        super().__init__()
        self.client = client
        self.context = context
        self.text = text
        
    def run(self):
        msg, action = self.client.get_action(self.context, self.text)
        self.finished.emit(msg, action)


class VisionWorker(QThread):
    """Runs Gemini's native vision in a background thread."""
    finished = pyqtSignal(str)
    
    def __init__(self, gemini_client, context, text):
        super().__init__()
        self.gemini_client = gemini_client
        self.context = context
        self.text = text

    def run(self):
        msg, _ = self.gemini_client.describe_image(self.context, self.text)
        self.finished.emit(msg)

class CaptureContextWorker(QThread):
    """Runs the OS context capture and UIA scraping in the background to prevent UI freezes."""
    finished = pyqtSignal(dict)
    
    def __init__(self, region):
        super().__init__()
        self.region = region

    def run(self):
        from context import capture_context
        # sys.coinit_flags = 2 ensures this thread handles COM properly
        import pythoncom
        pythoncom.CoInitialize()
        try:
            context_data = capture_context(self.region)
        finally:
            pythoncom.CoUninitialize()
        self.finished.emit(context_data)

class CoralApp(QObject):
    upload_result = pyqtSignal(str, str)  # msg, url
    trigger_overlay_sig = pyqtSignal()
    trigger_global_overlay_sig = pyqtSignal()
    trigger_record_sig = pyqtSignal()
    macro_done_sig = pyqtSignal(str)  # macro_name

    def __init__(self):
        super().__init__()
        self.upload_result.connect(self._on_upload_result)
        self.trigger_overlay_sig.connect(self.show_overlay)
        self.trigger_global_overlay_sig.connect(self.show_global_overlay)
        self.trigger_record_sig.connect(self.start_screen_record)
        self.macro_done_sig.connect(self._on_macro_done)
        
        self.qapp = QApplication(sys.argv)
        self.qapp.setStyle("Fusion")
        self.qapp.setQuitOnLastWindowClosed(False)

        # ── Style Qt's native tooltip to match Coral's dark theme ──────────
        self.qapp.setStyleSheet("""
            QToolTip {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #FF7A50;
                border-radius: 5px;
                padding: 4px 9px;
                font-weight: bold;
                font-size: 12px;
                font-family: 'Segoe UI';
                opacity: 240;
            }
        """)

        self.overlay = None
        self.popup = None
        self.latest_snip_context = None
        self.pinned_snips = []
        self.alchemy_filename = None  # Track if we are in data-extraction mode
        self.tray_icon = None
        
        # Core components
        # Core components
        from settings_manager import SettingsManager
        sm = SettingsManager()
        prov = sm.get("model_provider", "Groq")
        if prov == "Gemini":
            from gemini_client import GeminiClient
            self.ai_client = GeminiClient()
        else:
            from groq_client import GroqClient
            self.ai_client = GroqClient()
            
        from executor import ActionExecutor
        from undo_manager import UndoManager
        self.executor = ActionExecutor()
        self.undo_manager = UndoManager()
        self.pinned_snips = []
        
        self.pending_action = None

    def _force_activate(self, widget):
        """Force-activate a Qt.Tool window so it receives keyboard focus without Alt-Tab."""
        widget.show()
        widget.raise_()
        widget.activateWindow()
        # Defer Win32 focus-steal slightly to let the native window handle initialize
        from PyQt5.QtCore import QTimer
        def _steal_focus():
            try:
                # Guard: widget may have been closed/deleted before this timer fires
                import sip
                if sip.isdeleted(widget) or not widget.isVisible():
                    return
                widget.raise_()
                widget.activateWindow()
                widget.setFocus()
                import ctypes
                hwnd = int(widget.winId())
                # AttachThreadInput trick for reliable SetForegroundWindow
                fgThread = ctypes.windll.user32.GetWindowThreadProcessId(
                    ctypes.windll.user32.GetForegroundWindow(), None)
                curThread = ctypes.windll.kernel32.GetCurrentThreadId()
                if fgThread != curThread:
                    ctypes.windll.user32.AttachThreadInput(fgThread, curThread, True)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.AttachThreadInput(fgThread, curThread, False)
                else:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        QTimer.singleShot(100, _steal_focus)

    @pyqtSlot(str, str)
    def _on_upload_result(self, msg, url):
        """Called on main thread after a background upload finishes."""
        if url:
             from PyQt5.QtWidgets import QApplication
             QApplication.clipboard().setText(url)
        if self.popup:
            self.popup.append_message("Coral", msg)

    @pyqtSlot(str)
    def _on_macro_done(self, macro_name):
        """Called on main thread when macro recording finishes (Esc pressed)."""
        if self.popup:
            self.popup.append_message("Coral",
                f"✅ Macro <b>'{macro_name}'</b> recorded successfully!")

    def run(self):
        # Auto-cleanup vault on startup based on settings
        self._auto_vault_cleanup()

        # Start clipboard watcher
        self._start_clipboard_watcher()

        # Setup system tray
        threading.Thread(target=self.run_tray, daemon=True).start()

        # Setup hotkey
        self.setup_hotkeys()
        
        # Start PyQt Event Loop
        logger.info(f"{utils.APP_NAME} started. Snip: {utils.HOTKEY_SNIP} | Global: {utils.HOTKEY_GLOBAL} | Record: {utils.HOTKEY_RECORD}")
        sys.exit(self.qapp.exec_())

    def _auto_vault_cleanup(self):
        """Silently prune vault entries on startup based on vault_cleanup_days setting."""
        from settings_manager import SettingsManager
        days = SettingsManager().get("vault_cleanup_days", 7)
        if not days or days == 0:
            return  # "Never" — skip
        try:
            result = self.executor.execute_action({"action": "vault_cleanup", "days": days})
            if result.get("success"):
                logger.info(f"Vault auto-cleanup: {result.get('message', '')}")
        except Exception as e:
            logger.warning(f"Vault auto-cleanup failed: {e}")

    def _start_clipboard_watcher(self):
        """Background thread that saves any new Ctrl+C text to the scratchpad automatically."""
        import time
        sp_path = os.path.join(os.path.dirname(__file__), "coral_scratchpad.txt")
        _last_clip = [""]

        def _watch():
            while True:
                try:
                    cb = self.qapp.clipboard()
                    text = cb.text().strip()
                    if text and text != _last_clip[0] and len(text) < 5000:
                        _last_clip[0] = text
                        with open(sp_path, "a", encoding="utf-8") as f:
                            import datetime
                            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            f.write(f"[{ts}]\n{text}\n\n")
                except Exception:
                    pass
                time.sleep(1)

        threading.Thread(target=_watch, daemon=True).start()

    def run_tray(self):

        icon_image = Image.new('RGB', (64, 64), color=(30, 30, 30))
        d = ImageDraw.Draw(icon_image)
        d.text((10, 25), "Coral", fill=(255, 127, 80))

        menu = pystray.Menu(
            pystray.MenuItem('Coral Assistant', lambda icon, item: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Quit Coral', self.quit_app),
        )
        self.tray_icon = pystray.Icon("Coral", icon_image, "Coral Assistant", menu)
        # Double-click also quits (helpful if menu doesn't appear on first try)
        self.tray_icon.run()

    def quit_app(self, *args):
        logger.info("Quitting Coral...")
        if self.tray_icon:
            self.tray_icon.stop()
        if hasattr(self, 'hotkey_listener'):
            try: self.hotkey_listener.stop()
            except Exception: pass
        self.qapp.quit()
        import os; os._exit(0)   # Force-kill any lingering threads
        
    def setup_hotkeys(self):
        from settings_manager import SettingsManager
        settings = SettingsManager()
        h_snip = settings.get("hotkey_snip", utils.HOTKEY_SNIP)
        h_global = settings.get("hotkey_global", utils.HOTKEY_GLOBAL)
        h_record = settings.get("hotkey_record", utils.HOTKEY_RECORD)
        
        import keyboard
        def _clean(hk): return hk.replace('<', '').replace('>', '')
        
        try:
            keyboard.add_hotkey(_clean(h_snip), self.trigger_snip)
            keyboard.add_hotkey(_clean(h_global), self.trigger_global)
            keyboard.add_hotkey(_clean(h_record), self.trigger_record)
        except Exception as e:
            logger.error(f"Failed to bind hotkeys: {e}")

    def trigger_snip(self):
        import time; now = time.time()
        if hasattr(self, '_last_hk_time') and now - getattr(self, '_last_hk_time', 0) < 0.5: return
        self._last_hk_time = now
        try:
            import win32gui, utils
            utils.PREV_HWND = win32gui.GetForegroundWindow()
        except: pass
        self.trigger_overlay_sig.emit()
    
    def trigger_global(self):
        import time; now = time.time()
        if hasattr(self, '_last_hk_time') and now - getattr(self, '_last_hk_time', 0) < 0.5: return
        self._last_hk_time = now
        try:
            import win32gui, utils
            utils.PREV_HWND = win32gui.GetForegroundWindow()
        except: pass
        self.trigger_global_overlay_sig.emit()
        
    def trigger_record(self):
        import time; now = time.time()
        if hasattr(self, '_last_hk_time') and now - getattr(self, '_last_hk_time', 0) < 0.5: return
        self._last_hk_time = now
        try:
            import win32gui, utils
            utils.PREV_HWND = win32gui.GetForegroundWindow()
        except: pass
        self.trigger_record_sig.emit()
        
    from PyQt5.QtCore import pyqtSlot
    def _cleanup_all_overlays(self):
        for attr in ["overlay", "global_overlay", "record_overlay"]:
            if hasattr(self, attr) and getattr(self, attr):
                obj = getattr(self, attr)
                try: obj.hide_overlay()
                except: pass
                obj.deleteLater()
                setattr(self, attr, None)

    @pyqtSlot()
    def show_overlay(self):
        if self.popup:
            try:
                if hasattr(self, 'worker') and self.worker:
                    self.worker.finished.disconnect()
            except: pass
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
            
        self._cleanup_all_overlays()
        
        self.overlay = SelectionOverlay(self.on_snip_completed)
        self.overlay.showFullScreen()
        self.overlay.raise_()
        self.overlay.activateWindow()
        self.overlay.setFocus()
    
    @pyqtSlot()
    def start_screen_record(self):
        logger.info("Triggering Screen Recorder Selection...")
        if self.popup:
            try:
                if hasattr(self, 'worker') and self.worker:
                    self.worker.finished.disconnect()
            except: pass
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
            
        self._cleanup_all_overlays()

        self.record_overlay = SelectionOverlay(self.on_record_snip_completed)
        self.record_overlay.showFullScreen()
        self.record_overlay.raise_()
        self.record_overlay.activateWindow()
        self.record_overlay.setFocus()

    def on_record_snip_completed(self, region):
        logger.info(f"Record region selected: {region}")
        from PyQt5.QtCore import QRect
        from recording import RecordingControlPanel
        rect = QRect(region[0], region[1], region[2], region[3])
        
        # Don't proceed if it's an accidental tiny click
        if rect.width() < 50 or rect.height() < 50:
            logger.info("Recording area too small, cancelling.")
            return
            
        self.recording_panel = RecordingControlPanel(rect)
        self.recording_panel.recording_finished.connect(self.on_recording_saved)
        self.recording_panel.closed.connect(lambda: setattr(self, 'recording_panel', None))
        self.recording_panel.show()

    def on_recording_saved(self, path):
        import subprocess
        # Open folder and select the newly created video file
        try:
            subprocess.Popen(f'explorer /select,"{path}"')
        except Exception as e:
            logger.error(f"Failed to open recording path: {e}")
        self.recording_panel = None

    @pyqtSlot()
    def show_global_overlay(self):
        if self.popup:
            try:
                if hasattr(self, 'worker') and self.worker:
                    self.worker.finished.disconnect()
            except: pass
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
            
        self._cleanup_all_overlays()
            
        self.global_overlay = SelectionOverlay(self.on_global_snip_completed)
        self.global_overlay.showFullScreen()
        self.global_overlay.raise_()
        self.global_overlay.activateWindow()
        self.global_overlay.setFocus()

    def on_global_snip_completed(self, region):
        logger.info(f"Global snip completed! Region: {region}")
        context_data = capture_context(region)
        
        self.ai_client.reset_history()
        self.pending_action = None
        
        if self.popup:
            try:
                # Disconnect worker signals to prevent background crashes
                if hasattr(self, 'worker') and self.worker:
                    self.worker.finished.disconnect()
            except:
                pass
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
            
        self.popup = ChatPopup(context_data)
        self.popup.user_message_sent.connect(self.handle_user_message)
        self._force_activate(self.popup)
        
    @pyqtSlot()
    def show_global_popup(self):
        if self.popup:
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
        
        # Keep this for any programmatic fallback invocation
        context_data = {
            "type": "global",
            "path": "",
            "items": [],
            "image": None
        }
        if hasattr(self, 'ai_client'):
            self.ai_client.reset_history()
        self.pending_action = None
        
        self.popup = ChatPopup(context_data)
        self.popup.user_message_sent.connect(self.handle_user_message)
        self._force_activate(self.popup)

    def on_snip_completed(self, region):
        logger.info(f"Snip completed! Region: {region}. Starting background context capture...")
        
        # Ensure any existing popup is closed
        if self.popup:
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None

        self.ai_client.reset_history()
        self.pending_action = None

        self.context_worker = CaptureContextWorker(region)
        self.context_worker.finished.connect(self._on_context_captured)
        self.context_worker.start()

    def _on_context_captured(self, context_data):
        from capture_suite import CaptureSuitePopup
        self.popup = CaptureSuitePopup(context_data, parent_app=self)
        self.popup.ask_ai.connect(self.handle_ask_ai)
        self._force_activate(self.popup)

    def handle_ask_ai(self, context_data):
        """Called when user clicks 'Ask AI' from the capture suite."""
        if self.popup:
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
            
        if hasattr(self, 'ai_client'):
            self.ai_client.reset_history()
        self.pending_action = None
        
        # Open standard ChatPopup (passing the snip image + metadata)
        self.popup = ChatPopup(context_data)
        self.popup.user_message_sent.connect(self.handle_user_message)
        self._force_activate(self.popup)
        self.popup.append_message("Coral", "I've received your snip. What would you like to know about it?")


        
    def handle_user_message(self, text):
        # Special case: Undo
        cmd = text.strip().lower()
        if cmd == "undo" or cmd == "undo that" or cmd == "restore" or cmd == "restore that":
            result = self.undo_manager.undo()
            self.popup.append_message("Coral", result)
            self.pending_action = None
            
            # Refresh context so AI sees updated file list
            current_path = self.popup.context_data.get("path", "")
            if current_path and os.path.isdir(current_path):
                self.popup.context_data["items"] = _get_folder_items(current_path)
            
            # Feed undo result into AI history
            self.ai_client.history.append({"role": "user", "content": "undo"})
            # Note: client histories differ, but this is a reasonable approximation
            return
            
        # Special case: Yes / confirm
        if cmd in ["yes", "y", "do it", "sure", "ok", "s"] and self.pending_action:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self._execute_pending)
            return
            
        # Special case: No / cancel
        if cmd in ["no", "n", "cancel", "stop"] and self.pending_action:
            self.popup.append_message("Coral", "Okay, cancelled.")
            self.pending_action = None
            return

        # Slash commands
        if cmd.startswith("/"):
            self._handle_slash_command(cmd, text)
            return

        # ── Visual query → route to Gemini's native vision ────────────────
        from groq_client import is_visual_query
        has_image = self.popup.context_data.get("image") is not None

        if has_image and is_visual_query(text):
            self.popup.set_loading(True)
            # Always use a fresh GeminiClient for vision, regardless of model_provider
            if not hasattr(self, '_gemini_vision'):
                from gemini_client import GeminiClient
                self._gemini_vision = GeminiClient()
            self.vision_worker = VisionWorker(self._gemini_vision, self.popup.context_data, text)
            self.vision_worker.finished.connect(self._on_vision_result)
            self.vision_worker.start()
            return

        # Regular request
        self.popup.set_loading(True)
        self.worker = AIWorker(self.ai_client, self.popup.context_data, text)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.start()

    def _execute_pending(self):
        actions_to_run = self.pending_action if isinstance(self.pending_action, list) else [self.pending_action]
        
        results_summary = []
        for act in actions_to_run:
            if not act: continue
            
            # Inject snip coordinates for desktop positioning
            if act.get("action") == "create_folder" and "region" in self.popup.context_data:
                act["snip_x"] = self.popup.context_data["region"].get("x")
                act["snip_y"] = self.popup.context_data["region"].get("y")

            result = self.executor.execute_action(act)
            msg = result.get("message", "Error")
            results_summary.append(msg)

            if result.get("success"):
                self.undo_manager.push(result.get("reverse_action"))

                if act.get("action") == "open_folder":
                    target_path = act.get("path", "")
                    name = act.get("name", "")
                    if name:
                        target_path = os.path.join(target_path, name)
                    target_path = os.path.normpath(target_path)
                    if os.path.isdir(target_path):
                        self.popup.context_data["path"] = target_path
                        self.popup.context_data["items"] = _get_folder_items(target_path)
                        self.popup.path_label.setText(f"Location: {target_path}")

                current_path = self.popup.context_data.get("path", "")
                if current_path and os.path.isdir(current_path):
                    self.popup.context_data["items"] = _get_folder_items(current_path)

            # We don't append here anymore. We will join them all at the end.
            results_summary[len(results_summary)-1] = msg

        # Append all macro results as a single bubble
        if results_summary:
            if len(results_summary) > 1:
                action_types = set(act.get("action") for act in actions_to_run if isinstance(act, dict))
                if len(action_types) == 1:
                    atype = list(action_types)[0]
                    names = [act.get("name") or act.get("from") or act.get("target") or "" for act in actions_to_run if isinstance(act, dict)]
                    names = [n for n in names if n]
                    
                    friendly_verbs = {
                        "delete_folder": "Sent folders to Recycle Bin",
                        "delete_file": "Sent files to Recycle Bin",
                        "create_folder": "Created folders",
                        "create_file": "Created files",
                        "move_file": "Moved items",
                        "copy_file": "Copied items"
                    }
                    verb = friendly_verbs.get(atype, f"Executed {atype} on")
                    if names:
                        combined_msg = f"{verb}: {', '.join(os.path.basename(n) for n in names)}"
                    else:
                        combined_msg = "<br>".join(results_summary)
                else:
                    combined_msg = "<br>".join(results_summary)
            else:
                combined_msg = results_summary[0]
                
            # Apply universal linkifier!
            current_path = self.popup.context_data.get("path", "")
            combined_msg = self._linkify_message(combined_msg, actions_to_run, current_path)
            self.popup.append_message("Coral", combined_msg)

            if result.get("new_image"):
                self.popup.context_data["image"] = result["new_image"]
                self.popup.refresh_image_preview()
        
        if results_summary:
            result_text = " | ".join(results_summary)
            self.ai_client.append_history("user", "ok")
            self.ai_client.append_history("assistant", f'{{"message": "{result_text}", "action_json": null}}')
                        
        self.pending_action = None

    def _on_vision_result(self, description):
        """Called when Gemini's visual analysis completes."""
        if not self.popup:
            return
        self.popup.set_loading(False)
        self.popup.append_message("Coral", description)
        # Feed into the main AI client's history so follow-up questions work
        self.ai_client.append_history("user", "[visual query]")
        self.ai_client.append_history("assistant", description)

    def _linkify_message(self, message, action_json, current_path):
        """Finds target names in action_json and turns them into clickable links in the message."""
        if not message or not current_path:
            return message
            
        actions = action_json if isinstance(action_json, list) else ([action_json] if action_json else [])
        
        # Collect all possible target names from actions
        names_to_link = set()
        for act in actions:
            if not isinstance(act, dict): continue
            
            # Extract name, new_path, from, etc.
            for key in ["name", "new_path", "from", "target"]:
                val = act.get(key)
                if val and isinstance(val, str):
                    names_to_link.add(os.path.basename(val))
                    
        # Add all existing files and folders in the current directory!
        if os.path.exists(current_path):
            try:
                for entry in os.scandir(current_path):
                    if entry.name in message:
                        names_to_link.add(entry.name)
            except Exception:
                pass
                    
        import re
        # Sort names by length descending so we replace "test.txt" before "test"
        names_to_link = sorted(list(names_to_link), key=len, reverse=True)
        
        # Replace occurrences in message
        for name in names_to_link:
            if not name: continue
            if name in message:
                full_path = os.path.join(current_path, name)
                
                # Only linkify if the file actually exists right now.
                # This prevents deleted files from showing up as dead links in the result message.
                if os.path.exists(full_path):
                    uri = full_path.replace("\\", "/")
                    link = f"<a href='file:///{uri}' style='color:#88c0d0;'>{name}</a>"
                    # Use regex to replace whole words, making sure we don't double-replace inside tags
                    # (?<!>) avoids replacing inside HTML tags if it's already linked
                    pattern = rf"(?<!>)\b{re.escape(name)}\b"
                    message = re.sub(pattern, link, message)
        return message

    def on_ai_response(self, message, action_json):
        if not self.popup:
            return
        self.popup.set_loading(False)
        # --- DATA ALCHEMY INTERCEPTOR ---
        # Only trigger if alchemy was requested AND the AI response isn't a "not found" error
        is_error = any(x in message.lower() for x in ["could not find", "no code", "no table", "not found", "error"])
        if self.alchemy_filename and not action_json and not is_error:
            # The AI has returned the cleaned code/table in the 'message'
            path = self.popup.context_data.get("path", os.path.expanduser("~/Desktop"))
            target_file = os.path.join(path, self.alchemy_filename)
            
            # Simple save action
            res = self.executor.execute_action({
                "action": "create_file", 
                "path": path, 
                "name": self.alchemy_filename
            })
            if res.get("success"):
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(message)
                self.popup.append_message("Coral", f"Source transmutation complete. Created <a href='file:///{target_file.replace('\\','/')}'>{self.alchemy_filename}</a>")
            else:
                self.popup.append_message("Coral", f"Alchemy failed: {res.get('message')}")
            
            self.alchemy_filename = None
            return
        # -------------------------------
        
        from settings_manager import SettingsManager
        settings = SettingsManager()
        current_path = self.popup.context_data.get("path", "")
        message = self._linkify_message(message, action_json, current_path)
        
        # Handle macro (list of actions)
        if isinstance(action_json, list) and action_json:
            self.pending_action = action_json
            has_delete = any(a.get("action") in ["delete_file", "delete_folder"] for a in action_json if isinstance(a, dict))
            
            if has_delete and settings.get("confirm_deletes", True):
                self.popup.append_message("Coral", message)
                return
            if settings.get("confirm_actions", True):
                self.popup.append_message("Coral", message)
                return
            
            # Auto-execute: skip AI intent message, results will show
            self._execute_pending()
            
        elif isinstance(action_json, dict):
            action_type = action_json.get("action")
            if action_type and action_type != "null" and action_type != "None":
                is_delete = action_type in ["delete_file", "delete_folder"]
                needs_confirm = (is_delete and settings.get("confirm_deletes", True)) or (not is_delete and settings.get("confirm_actions", True))
                self.pending_action = action_json
                if needs_confirm:
                    self.popup.append_message("Coral", message)
                else:
                    # Auto-execute: skip AI intent message
                    self._execute_pending()
            else:
                self.popup.append_message("Coral", message)
                self.pending_action = None
        else:
            self.popup.append_message("Coral", message)
            self.pending_action = None
    def _handle_slash_command(self, cmd_line, full_text):
        if not self.popup: return
        parts = full_text.strip().split()
        cmd_word = parts[0].lower() if parts else ""
        args = parts[1:]
        ctx_path = self.popup.context_data.get("path", "")

        if cmd_word in ["/help", "/?", "?"]:
            help_text = """
<b style='color: #FF7F50;'>File Operations</b><br>
/create_folder, /create_file, /delete, /copy, /duplicate, /move, /rename<br><br>
<b style='color: #FF7F50;'>Folder Operations</b><br>
/open, /arrange, /flatten, /clean, /shortcut, /zip, /unzip<br><br>
<b style='color: #FF7F50;'>Information</b><br>
/info, /usage, /duplicates, /search_inside [query]<br><br>
<b style='color: #FF7F50;'>Tags</b><br>
/tag, /all_tags<br><br>
<b style='color: #FF7F50;'>Image & Vision</b><br>
/color, /qr, /remove_bg, /blur, /wallpaper<br><br>
<b style='color: #FF7F50;'>Vault (Persistent Memory)</b><br>
/note [text], /vault [n]<br><br>
<b style='color: #FF7F50;'>System Automation</b><br>
/kill [app], /vol, /mute, /lock, /sleep, /empty_trash, /timer, /dark_mode, /sysinfo<br><br>
<b style='color: #FF7F50;'>Macros (Offline RPA)</b><br>
/macro_record [name], /macro_play [name]<br><br>
<b style='color: #FF7F50;'>Utilities</b><br>
/extract, /convert, /bulk_rename, /undo, /pin, /qr, /link, /help<br><br>
<i>Tip: You don't need slashes! Coral understands English natively.</i>"""
            self.popup.append_message("Coral", help_text)
            return

        if cmd_word == "/undo":
            result = self.undo_manager.undo()
            self.popup.append_message("Coral", result)
            cp = self.popup.context_data.get("path", "")
            if cp and os.path.isdir(cp):
                self.popup.context_data["items"] = _get_folder_items(cp)
            return

        action_json = None
        message = ""

        if cmd_word == "/create_folder":
            name = " ".join(args) if args else ""
            if not name: self.popup.append_message("Coral", "Usage: /create_folder name"); return
            action_json = {"action": "create_folder", "name": name, "path": ctx_path}
            message = f"Creating folder '{name}'"

        elif cmd_word == "/create_file":
            name = " ".join(args) if args else ""
            if not name: self.popup.append_message("Coral", "Usage: /create_file name"); return
            action_json = {"action": "create_file", "name": name, "path": ctx_path}
            message = f"Creating file '{name}'"

        elif cmd_word == "/delete":
            name = " ".join(args) if args else ""
            if not name: self.popup.append_message("Coral", "Usage: /delete name"); return
            target = os.path.join(ctx_path, name)
            if os.path.isdir(target):
                action_json = {"action": "delete_folder", "name": name, "path": ctx_path}
            else:
                action_json = {"action": "delete_file", "name": name, "path": ctx_path}
            message = f"Deleting '{name}'"

        elif cmd_word == "/copy":
            if len(args) < 2: self.popup.append_message("Coral", "Usage: /copy source destination"); return
            src_name, dst_name = args[0], " ".join(args[1:])
            dst_path = dst_name if os.path.isabs(dst_name) else os.path.join(ctx_path, dst_name)
            action_json = {"action": "copy_file", "name": src_name, "path": ctx_path, "destination": dst_path}
            message = f"Copying '{src_name}' to '{dst_name}'"

        elif cmd_word == "/move":
            if len(args) < 2: self.popup.append_message("Coral", "Usage: /move source destination"); return
            src_name, dst_name = args[0], " ".join(args[1:])
            src_path = os.path.join(ctx_path, src_name)
            dst_path = dst_name if os.path.isabs(dst_name) else os.path.join(ctx_path, dst_name)
            action_json = {"action": "move_file", "from": src_path, "to": dst_path}
            message = f"Moving '{src_name}' to '{dst_name}'"

        elif cmd_word == "/rename":
            if len(args) < 2: self.popup.append_message("Coral", "Usage: /rename old new"); return
            old_name, new_name = args[0], " ".join(args[1:])
            action_json = {"action": "rename_file", "old_path": os.path.join(ctx_path, old_name), "new_path": os.path.join(ctx_path, new_name)}
            message = f"Renaming '{old_name}' to '{new_name}'"

        elif cmd_word == "/duplicate":
            name = " ".join(args) if args else ""
            if not name: self.popup.append_message("Coral", "Usage: /duplicate name"); return
            action_json = {"action": "duplicate_file", "name": name, "path": ctx_path}
            message = f"Duplicating '{name}'"

        elif cmd_word == "/open":
            name = " ".join(args) if args else ""
            action_json = {"action": "open_folder", "name": name, "path": ctx_path}
            message = f"Opening '{name}'" if name else f"Opening {ctx_path}"

        elif cmd_word == "/arrange":
            action_json = {"action": "arrange_by_type", "path": ctx_path}
            message = "Arranging files by type"

        elif cmd_word == "/flatten":
            action_json = {"action": "flatten_folder", "path": ctx_path}
            message = "Flattening folder"

        elif cmd_word == "/clean":
            action_json = {"action": "clean_empty", "path": ctx_path}
            message = "Cleaning empty folders"

        elif cmd_word == "/shortcut":
            target = " ".join(args) if args else ""
            if not target: self.popup.append_message("Coral", "Usage: /shortcut target"); return

            # Check if target is a local file/folder first
            local_target = os.path.join(ctx_path, target) if not os.path.isabs(target) else target
            if os.path.exists(local_target):
                # Direct local file/folder — create shortcut immediately
                action_json = {"action": "create_shortcut", "target": local_target, "location": ctx_path, "shortcut_name": os.path.basename(local_target)}
                message = f"Creating shortcut for '{os.path.basename(local_target)}'"
            else:
                # Not a local path — try auto-discovering via Everything
                resolved_path = None
                display_name = target
                try:
                    if hasattr(self, 'executor') and self.executor.search_api:
                        # Try app discovery first (like open_in_app does)
                        app_path = self.executor._auto_find_app(target)
                        if app_path:
                            resolved_path = app_path
                        else:
                            # Search for exe/lnk
                            results = self.executor.search_api.search(f'"{target}" ext:exe;lnk', limit=5)
                            if not results:
                                results = self.executor.search_api.search(f'{target}.exe', limit=5)
                            if results:
                                resolved_path = results[0]
                except Exception:
                    pass

                if resolved_path and os.path.exists(resolved_path):
                    display_name = os.path.basename(resolved_path)
                    short_name = os.path.splitext(display_name)[0]
                    self.popup.append_message("Coral",
                        f"Did you mean <b>{short_name}</b>?<br>"
                        f"<span style='color:#888;font-size:11px;'>{resolved_path}</span><br><br>"
                        f"Say <b>yes</b> to create the shortcut.")
                    self.pending_action = {
                        "action": "create_shortcut",
                        "target": resolved_path,
                        "location": ctx_path,
                        "shortcut_name": short_name
                    }
                    return
                else:
                    # Nothing found — fall back to raw target
                    action_json = {"action": "create_shortcut", "target": target, "location": ctx_path, "shortcut_name": target}
                    message = f"Creating shortcut for '{target}' (target not found on system, shortcut may be broken)"

        elif cmd_word == "/info":
            name = " ".join(args) if args else ""
            if not name: self.popup.append_message("Coral", "Usage: /info name"); return
            action_json = {"action": "file_info", "name": name, "path": ctx_path}
            message = f"Getting info for '{name}'"

        elif cmd_word == "/usage":
            action_json = {"action": "disk_usage", "path": ctx_path}
            message = "Calculating disk usage"

        elif cmd_word == "/duplicates":
            action_json = {"action": "find_duplicates", "path": ctx_path}
            message = "Scanning for duplicates"

        elif cmd_word == "/convert":
            if len(args) < 2: self.popup.append_message("Coral", "Usage: /convert file format"); return
            action_json = {"action": "convert_file", "file_name": args[0], "target_extension": args[1], "path": ctx_path}
            message = f"Converting '{args[0]}' to .{args[1]}"

        elif cmd_word == "/bulk_rename":
            prefix = " ".join(args) if args else "file"
            action_json = {"action": "bulk_rename", "path": ctx_path, "prefix": prefix}
            message = f"Bulk renaming with prefix '{prefix}'"

        elif cmd_word == "/tag":
            if len(args) < 2: self.popup.append_message("Coral", "Usage: /tag file tag"); return
            action_json = {"action": "add_tag", "name": args[0], "path": ctx_path, "tag": " ".join(args[1:])}
            message = f"Tagging '{args[0]}' as '{' '.join(args[1:])}'"

        elif cmd_word == "/untag":
            if not args or len(args) < 2: self.popup.append_message("Coral", "Usage: /untag file tag"); return
            action_json = {"action": "remove_tag", "name": args[0], "path": ctx_path, "tag": " ".join(args[1:])}
            message = f"Removing tag '{' '.join(args[1:])}' from '{args[0]}'"

        elif cmd_word == "/all_tags":
            action_json = {"action": "list_tags", "path": ctx_path}
            message = "Listing all tags"

        elif cmd_word == "/extract":
            image_data = self.popup.context_data.get("image")
            action_json = {"action": "extract_text", "image": image_data}
            message = "Running OCR on sniped region..."

        elif cmd_word == "/link":
            image_data = self.popup.context_data.get("image")
            if not image_data:
                self.popup.append_message(
                    "Coral",
                    "No snip to share. Use <b>Ctrl+Shift+S</b> to capture a region first, then run /link."
                )
                return
            # Run upload in background
            import threading
            from io import BytesIO as _BytesIO
            _img = image_data
            _self = self

            def _upload():
                try:
                    import requests
                    buf = _BytesIO()
                    _img.save(buf, format="PNG")
                    buf.seek(0)
                    r = requests.post(
                        "https://tmpfiles.org/api/v1/upload",
                        files={"file": ("coral_snip.png", buf, "image/png")},
                        timeout=20
                    )
                    if r.status_code == 200:
                        import json
                        url = json.loads(r.text)["data"]["url"].replace("http://", "https://")
                        
                        _self.upload_result.emit(
                            f"Link ready: <a href='{url}' style='color:#88c0d0;'>{url}</a>  [COPY_BTN:{url}]",
                            url
                        )
                    else:
                        _self.upload_result.emit(f"Upload failed: server returned {r.status_code}.", "")
                except Exception as e:
                    _self.upload_result.emit(f"Upload error: {e}", "")

            threading.Thread(target=_upload, daemon=True).start()
            return  # Don't route through execute_action

        elif cmd_word == "/sysinfo":
            action_json = {"action": "sys_info"}
            message = "Fetching System Information..."

        elif cmd_word == "/macro_record":
            name = " ".join(args) if args else "quick_macro"
            # Use a signal-based callback so the message is delivered on the main thread
            _self = self
            def _on_macro_done(macro_name):
                _self.macro_done_sig.emit(macro_name)
            action_json = {"action": "macro_record", "name": name, "_done_cb": _on_macro_done}
            message = f"Recording macro '{name}'... Press Esc to stop."

        elif cmd_word == "/macro_play":
            name = " ".join(args) if args else "quick_macro"
            action_json = {"action": "macro_play", "name": name}
            message = f"Playing macro '{name}'..."

        elif cmd_word == "/dark_mode":
            action_json = {"action": "toggle_dark_mode"}
            message = "Toggling Windows Dark Mode..."

        elif cmd_word == "/color":
            image_data = self.popup.context_data.get("image")
            action_json = {"action": "color_picker", "image": image_data}
            message = "Extracting dominant colors..."

        elif cmd_word == "/pin" or cmd_word == "/pin_live":
            is_live_request = (cmd_word == "/pin_live")
            if self.popup:
                self.popup.hide()
                
            def _pin_completed(region):
                from context import capture_context
                context_data = capture_context(region)
                image_data = context_data.get("image")
                if image_data and region:
                    from overlay import PinnedSnip
                    new_pin = PinnedSnip(image_data, region, is_live=is_live_request, context=context_data)
                    self.pinned_snips.append(new_pin)
                self.live_overlay = None
                
                if self.popup and self.popup.isHidden():
                    label = "Live screen region" if is_live_request else "Static screen region"
                    self.popup.append_message("Coral", f"{label} pinned successfully.")
                    self.popup.show()
                    self.popup.activateWindow()

            if getattr(self, "live_overlay", None):
                self.live_overlay.close()
                
            from overlay import SelectionOverlay
            self.live_overlay = SelectionOverlay(_pin_completed)
            self.live_overlay.showFullScreen()
            return

        elif cmd_word == "/qr":
            image_data = self.popup.context_data.get("image")
            action_json = {"action": "qr_scanner", "image": image_data}
            message = "Scanning for QR/Barcodes..."
            
        elif cmd_word == "/blur":
            image_data = self.popup.context_data.get("image")
            action_json = {"action": "blur_snip", "image": image_data}
            message = "Applying blur to snip..."

        elif cmd_word == "/remove_bg":
            image_data = self.popup.context_data.get("image")
            action_json = {"action": "remove_bg", "image": image_data}
            message = "Removing background... (This may take a moment)"

        elif cmd_word == "/vol":
            level = args[0] if args else "50"
            action_json = {"action": "set_volume", "level": level}
            message = f"Setting system volume to {level}%..."

        elif cmd_word == "/mute":
            action_json = {"action": "set_volume", "mute": True}
            message = "Muting system audio..."

        elif cmd_word == "/lock":
            action_json = {"action": "system_power", "mode": "lock"}
            message = "Locking workstation..."

        elif cmd_word == "/sleep":
            action_json = {"action": f"system_power", "mode": "sleep"}
            message = "Putting system to sleep..."

        elif cmd_word == "/empty_trash":
            action_json = {"action": "empty_trash"}
            message = "Emptying Recycle Bin..."

        elif cmd_word == "/timer":
            try:
                time_val = float(args[0]) if args else 60
                unit = args[1].lower() if len(args) > 1 else "sec"
                label_parts = args[2:] if len(args) > 2 else []
                label = " ".join(label_parts) if label_parts else "Timer done!"
                
                if unit == "min": seconds = int(time_val * 60)
                elif unit == "hr": seconds = int(time_val * 3600)
                else: seconds = int(time_val)
            except:
                seconds = 60
                label = "Timer done!"
                
            action_json = {"action": "set_timer", "seconds": seconds, "label": label}
            message = f"Setting timer for {int(time_val)} {unit}..."

        elif cmd_word in ["/note", "/scratchpad"]:
            txt = " ".join(args)
            action_json = {"action": "scratchpad", "text": txt}
            message = "Saving note to vault..."

        # ── NEW BATCH-1 COMMANDS ──────────────────────────────────────────────

        elif cmd_word == "/kill":
            name = " ".join(args) if args else ""
            if not name:
                self.popup.append_message("Coral", "Usage: /kill [app name]  e.g. /kill chrome")
                return
            action_json = {"action": "kill_app", "name": name}
            message = f"Force-killing '{name}'..."

        elif cmd_word == "/zip":
            name = " ".join(args) if args else ""
            if not name:
                self.popup.append_message("Coral", "Usage: /zip [file or folder name]")
                return
            action_json = {"action": "zip_files", "name": name, "path": ctx_path}
            message = f"Compressing '{name}'..."

        elif cmd_word == "/unzip":
            name = " ".join(args) if args else ""
            if not name:
                self.popup.append_message("Coral", "Usage: /unzip [file.zip]")
                return
            action_json = {"action": "unzip_files", "name": name, "path": ctx_path}
            message = f"Extracting '{name}'..."

        elif cmd_word == "/wallpaper":
            image_data = self.popup.context_data.get("image")
            action_json = {"action": "set_wallpaper", "image": image_data}
            message = "Setting snip as desktop wallpaper..."

        elif cmd_word == "/search_inside":
            query = " ".join(args) if args else ""
            if not query:
                self.popup.append_message("Coral", "Usage: /search_inside [query]  e.g. /search_inside TODO")
                return
            action_json = {"action": "search_inside", "query": query, "path": ctx_path}
            message = f"Searching inside files for '{query}'..."

        elif cmd_word == "/vault":
            n = int(args[0]) if args and args[0].isdigit() else 5
            action_json = {"action": "vault_read", "n": n}
            message = f"Reading last {n} vault entries..."

        elif cmd_word == "/global":
            self.popup.context_data["type"] = "global"
            self.popup.context_data["path"] = ""
            self.popup.context_data["items"] = []
            self.popup.context_data["image"] = None
            self.popup.path_label.setText("Mode: Global (system-wide)")
            self.popup.img_label.setFixedHeight(0)
            self.popup.append_message("Coral", "Switched to global mode. Chat scope is now system-wide.")
            return

        elif cmd_word == "/code":
            self.alchemy_filename = args[0] if args else "extracted_code.py"
            prompt = "Extract and clean the code from this snip. Return ONLY the code in the message."
            self.popup.set_loading(True)
            self.worker = AIWorker(self.ai_client, self.popup.context_data, prompt)
            self.worker.finished.connect(self.on_ai_response)
            self.worker.start()
            return

        elif cmd_word == "/table":
            self.alchemy_filename = args[0] if args else "extracted_table.csv"
            prompt = "Extract the table from this snip and convert it to CSV format. Return ONLY the CSV in the message."
            self.popup.set_loading(True)
            self.worker = AIWorker(self.ai_client, self.popup.context_data, prompt)
            self.worker.finished.connect(self.on_ai_response)
            self.worker.start()
            return

        else:
            self.popup.append_message("Coral", f"Unknown command: {cmd_word}. Type /help for list.")
            return

        if action_json:
            from settings_manager import SettingsManager
            settings = SettingsManager()
            is_delete = action_json.get("action") in ["delete_file", "delete_folder"]
            self.pending_action = action_json

            if is_delete and settings.get("confirm_deletes", True):
                # Ask as a clear question — show filename as clickable link
                _target = action_json.get("name") or os.path.basename(action_json.get("path", ""))
                _full_path = os.path.join(
                    action_json.get("path", self.popup.context_data.get("path", "")),
                    _target
                )
                _uri = _full_path.replace("\\", "/")
                _link = f"<a href='file:///{_uri}' style='color:#88c0d0;'>{_target}</a>"
                self.popup.append_message(
                    "Coral",
                    f"Delete {_link}?"
                )
            elif action_json.get("action") in ["macro_record", "macro_play"]:
                # Macros show their status message then execute immediately
                self.popup.append_message("Coral", message)
                self._execute_pending()
            elif settings.get("confirm_actions", True):
                # Confirm mode: show intent message, wait for yes
                self.popup.append_message("Coral", message)
            else:
                # Auto-execute: show only the executor result, not the "doing" message
                self._execute_pending()

if __name__ == '__main__':
    # Install a global exception hook so unhandled exceptions in threads/slots
    # get logged instead of silently crashing the process
    import traceback as _tb

    def _global_excepthook(exc_type, exc_value, exc_tb):
        logger.error("".join(_tb.format_exception(exc_type, exc_value, exc_tb)))

    sys.excepthook = _global_excepthook

    # PyQt5 can also crash from unhandled exceptions in slots —
    # monkey-patch QApplication to catch those too
    def _qt_message_handler(msg_type, context, msg):
        if msg_type == 3:  # QtFatalMsg
            logger.error(f"Qt Fatal: {msg}")
        elif msg_type == 2:  # QtCriticalMsg
            logger.error(f"Qt Critical: {msg}")
        elif msg_type == 1:  # QtWarningMsg
            # Suppress noisy but harmless warnings
            if "QMetaObject::invokeMethod" in msg or "QLayout" in msg:
                return
            logger.warning(f"Qt Warning: {msg}")

    from PyQt5.QtCore import qInstallMessageHandler
    qInstallMessageHandler(_qt_message_handler)

    app = CoralApp()
    app.run()
