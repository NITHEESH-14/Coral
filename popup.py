from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QScrollArea, QFrame, QApplication, QCompleter, QSizeGrip, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PIL import ImageGrab, Image
from io import BytesIO
import utils

class ChatPopup(QWidget):
    # Emits the text typed by the user
    user_message_sent = pyqtSignal(str)

    def __init__(self, context_data):
        super().__init__()
        self.context_data = context_data
        # Determine screen bounds to avoid off-screen
        screen_rect = QApplication.desktop().screenGeometry()
        
        from settings_manager import SettingsManager
        settings = SettingsManager()
        saved_size = settings.get("popup_size", [350, 450])
        popup_width = max(300, saved_size[0])
        popup_height = max(100, saved_size[1])
        
        if context_data.get("type") == "global":
            px = int((screen_rect.width() - popup_width) / 2)
            py = int((screen_rect.height() - popup_height) / 2)
        else:
            # Calculate popup position based on snip region
            rect = context_data.get("region", {"x": 0, "y": 0, "w": 0, "h": 0})
            x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
            
            # Place to the right of the snip if possible, else to the left
            if x + w + popup_width + 20 <= screen_rect.width():
                px = x + w + 20
            else:
                px = x - popup_width - 20
                
            # Place near the top of the snip
            py = max(0, y)
            if py + popup_height > screen_rect.height():
                py = screen_rect.height() - popup_height - 20
            
        self.setGeometry(px, py, popup_width, popup_height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()

    def init_ui(self):
        from settings_manager import SettingsManager
        settings = SettingsManager()
        font_size = settings.get("base_font_size", 13)
        
        # Main layout container for rounded borders
        self.central_frame = QFrame(self)
        self.setObjectName("ChatWindow")
        self.setStyleSheet(f"""
            QWidget#ChatWindow {{
                background-color: rgba(1, 1, 1, 1);
            }}
            QFrame#MainFrame {{
                background-color: {utils.THEME['background']};
                border-radius: 16px;
                border: 1px solid #444;
            }}
            QWidget {{
                color: {utils.THEME['text']};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {utils.THEME['primary']};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #FF6633;
            }}
        """)
        self.central_frame.setObjectName("MainFrame")
        
        # Safe layout assignment
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.central_frame)
        
        layout = QVBoxLayout(self.central_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. Header (Brand + Settings + Close)
        header_title = QLabel(utils.APP_NAME)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        header_title.setFont(font)
        header_title.setStyleSheet(f"color: {utils.THEME['primary']};")
        
        settings_btn = QPushButton("\u2699")
        settings_btn.setFixedSize(30, 30)
        settings_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaa; font-size: 16px; padding: 0px; border: none; }
            QPushButton:hover { color: white; }
        """)
        settings_btn.clicked.connect(self.open_settings)
        
        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {utils.THEME['primary']}; font-weight: bold; padding: 0px; font-size: 14px; border: none; }}
            QPushButton:hover {{ color: white; background-color: transparent; }}
        """)
        close_btn.clicked.connect(self.close)

        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        self.header_frame.setFixedHeight(40)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        header_layout.addWidget(close_btn)
        layout.addWidget(self.header_frame)
        
        # 2. Image Preview
        self.img_label = QLabel()
        self.img_label.setFixedHeight(100)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet(f"background-color: {utils.THEME['surface']}; border-radius: 8px;")
        
        is_global = self.context_data.get("type") == "global"
        
        if not is_global and "image" in self.context_data and self.context_data["image"]:
            pil_img = self.context_data["image"]
            byte_io = BytesIO()
            pil_img.save(byte_io, format='PNG')
            byte_data = byte_io.getvalue()
            pixmap = QPixmap()
            pixmap.loadFromData(byte_data)
            scaled = pixmap.scaled(self.width() - 50, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled)
        elif is_global:
            self.img_label.setFixedHeight(0)  # Hide image area in global mode

        # 2.5 Path Label
        if is_global:
            path_str = "Mode: Global (system-wide)"
        else:
            path_str = self.context_data.get("path", "")
            if not path_str:
                path_str = "Location: Unknown / Unrecognized"
            else:
                path_str = f"Location: {path_str}"
            
        self.path_label = QLabel(path_str)
        path_font = QFont()
        path_font.setPointSize(9)
        self.path_label.setFont(path_font)
        self.path_label.setStyleSheet("color: #888; margin-top: 5px; margin-bottom: 5px;")
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setWordWrap(True)

        # 3. Chat History (Modern Bubble Layout)
        self.current_font_size = font_size
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_history.setStyleSheet(f"""
            QScrollArea {{
                background: transparent; border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {utils.THEME['primary']};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch() # Push everything up
        
        self.chat_history.setWidget(self.chat_content)
        
        # Keep track of message widgets for dynamically updating font sizes
        self.message_labels = []
        
        if is_global:
            self.append_message("Coral", "Global mode. What would you like to do?")
        else:
            self.append_message("Coral", "Context ready. Tell me what you'd like to do.")

        # 4. Input Area
        input_layout = QHBoxLayout()
        
        self.input_wrapper = QFrame()
        self.input_wrapper.setFixedHeight(36)
        self.input_wrapper.setStyleSheet(f"""
            QFrame {{
                background-color: {utils.THEME['surface']};
                border: 1px solid #444;
                border-radius: 15px;
            }}
        """)
        self.wrapper_layout = QHBoxLayout(self.input_wrapper)
        self.wrapper_layout.setContentsMargins(6, 0, 4, 0)
        self.wrapper_layout.setSpacing(4)
        
        # The main text input (shown when no command is active)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 6px 5px;
                font-size: 13px;
                color: {utils.THEME['text']};
            }}
        """)
        self.input_field.setPlaceholderText("Type a command or /help...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.textChanged.connect(self.on_text_changed)
        
        self.wrapper_layout.addWidget(self.input_field)
        
        self.active_command = None
        self.arg_fields = []
        self.dynamic_widgets = []
        self._ignoring_send = False
        
        # Multi-field definitions per command
        self.command_fields = {
            # ── File Management ───────────────────────────────────────────────
            "/create_folder": [{"type": "input", "ph": "folder name"}],
            "/create_file":   [{"type": "input", "ph": "file name"}],
            "/delete":        [{"type": "input", "ph": "file or folder"}],
            "/copy":          [{"type": "input", "ph": "file"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "destination"}],
            "/duplicate":     [{"type": "input", "ph": "file name"}],
            "/move":          [{"type": "input", "ph": "file"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "destination"}],
            "/rename":        [{"type": "input", "ph": "old name"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "new name"}],
            "/open":          [{"type": "input", "ph": "folder name"}],
            "/shortcut":      [{"type": "input", "ph": "target file"}],
            "/info":          [{"type": "input", "ph": "file name"}],
            "/zip":           [{"type": "input", "ph": "file or folder"}],
            "/unzip":         [{"type": "input", "ph": "file.zip"}],
            # ── Organisation ─────────────────────────────────────────────────
            "/bulk_rename":   [{"type": "input", "ph": "prefix"}],
            # ── Tags ─────────────────────────────────────────────────────────
            "/tag":           [{"type": "input", "ph": "file"}, {"type": "label", "text": "as"}, {"type": "input", "ph": "tag"}],
            "/untag":         [{"type": "input", "ph": "file"}, {"type": "label", "text": "remove"}, {"type": "input", "ph": "tag"}],
            # ── Image & Media ─────────────────────────────────────────────────
            "/convert":       [{"type": "input", "ph": "file"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "format"}],
            "/qr":            [{"type": "input", "ph": "text / URL to encode"}],
            # ── System Controls ───────────────────────────────────────────────
            "/vol":           [{"type": "input", "ph": "0–100"}],
            "/timer":         [{"type": "input", "ph": "Time"}, {"type": "select", "options": ["sec", "min", "hr"]}, {"type": "input", "ph": "Message (optional)"}],
            "/kill":          [{"type": "input", "ph": "app name (e.g. chrome)"}],
            # ── Utilities ────────────────────────────────────────────────────
            "/search_inside": [{"type": "input", "ph": "search query"}],
            "/vault":         [{"type": "input", "ph": "number of entries (default 5)"}],
            "/note":          [{"type": "input", "ph": "note text"}],
            "/macro_record":  [{"type": "input", "ph": "macro name"}],
            "/macro_play":    [{"type": "input", "ph": "macro name"}],
            "/code":          [{"type": "input", "ph": "filename (e.g. script.py)"}],
            "/table":         [{"type": "input", "ph": "filename (e.g. data.csv)"}],
        }

        self.no_arg_commands = [
            "/arrange", "/flatten", "/clean", "/usage", "/duplicates",
            "/all_tags", "/undo", "/help", "/global",
            "/extract", "/link", "/sysinfo", "/dark_mode",
            "/color", "/pin", "/pin_live", "/blur", "/remove_bg",
            "/mute", "/lock", "/sleep", "/empty_trash",
            "/wallpaper",
        ]

        # Dynamically generate autocomplete list from all registered components
        commands = list(self.command_fields.keys()) + self.no_arg_commands
        self.completer = QCompleter(commands, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchStartsWith)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        
        self.completer.popup().setStyleSheet(f"""
            QListView {{
                background-color: {utils.THEME['surface']};
                color: {utils.THEME['text']};
                border: 1px solid {utils.THEME['primary']};
                border-radius: 5px; padding: 2px 0px; font-size: 13px;
                outline: 0;
            }}
            QListView::item {{ padding: 6px 10px; margin: 0px; min-height: 20px; }}
            QListView::item:selected {{ background-color: {utils.THEME['primary']}; color: white; }}
            QListView::item:hover {{ background-color: #444; }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {utils.THEME['primary']};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)
        
        self.input_field.setCompleter(self.completer)
        self.completer.activated.connect(self.on_command_selected)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_wrapper)
        input_layout.addWidget(self.send_btn)
        
        # Manual edge resizing handles resizing now

        # Assemble
        layout.addLayout(header_layout)
        layout.addWidget(self.img_label)
        layout.addWidget(self.path_label)
        layout.addWidget(self.chat_history)
        layout.addLayout(input_layout)
        
        self.oldPos = self.pos()
        self.setMouseTracking(True)
        self.central_frame.setMouseTracking(True)
        self.central_frame.installEventFilter(self)
        
        from PyQt5.QtCore import QTimer
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._update_cursor)
        self._cursor_timer.start(200) # Throttled for stability
        
    def _update_cursor(self):
        if getattr(self, '_drag_active', False) or not self.isVisible():
            return
        from PyQt5.QtGui import QCursor
        from PyQt5.QtWidgets import QApplication
        gp = QCursor.pos()
        w = QApplication.widgetAt(gp)
        if w and w.window() is self:
            local_pos = self.mapFromGlobal(gp)
            r_dir = self.get_resize_dir(local_pos)
            if r_dir in [1, 2]: self.setCursor(Qt.SizeVerCursor)
            elif r_dir in [3, 4]: self.setCursor(Qt.SizeHorCursor)
            elif r_dir in [5, 6]: self.setCursor(Qt.SizeFDiagCursor)
            elif r_dir in [7, 8]: self.setCursor(Qt.SizeBDiagCursor)
            else: self.unsetCursor()
        else:
            self.unsetCursor()

    def refresh_image_preview(self):
        if "image" in self.context_data and self.context_data["image"]:
            pil_img = self.context_data["image"]
            from io import BytesIO
            byte_io = BytesIO()
            pil_img.save(byte_io, format='PNG')
            byte_data = byte_io.getvalue()
            pixmap = QPixmap()
            pixmap.loadFromData(byte_data)
            scaled = pixmap.scaled(self.width() - 50, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled)
            self.img_label.setFixedHeight(100)

    # --- Helper widget factories ---

    def _make_cmd_chip(self, text):
        chip = QLabel(text)
        chip.setStyleSheet(f"""
            QLabel {{
                background-color: {utils.THEME['primary']};
                color: white;
                padding: 2px 8px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        chip.setFixedHeight(24)
        return chip
    
    def _make_label_chip(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {utils.THEME['text_muted']};
                font-size: 11px;
                font-style: italic;
                padding: 0px 2px;
            }}
        """)
        label.setFixedHeight(24)
        return label
    
    def _make_arg_input(self, placeholder):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setStyleSheet(f"""
            QLineEdit {{
                background-color: #3A3A3A;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 12px;
                color: {utils.THEME['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {utils.THEME['primary']};
            }}
        """)
        field.setFixedHeight(26)
        field.returnPressed.connect(self.send_message)
        return field

    def _make_arg_select(self, options):
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #3A3A3A;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 12px;
                color: {utils.THEME['text']};
            }}
            QComboBox::drop-down {{
                border-left-width: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #3A3A3A;
                color: {utils.THEME['text']};
                selection-background-color: {utils.THEME['primary']};
                border: 1px solid {utils.THEME['primary']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {utils.THEME['primary']};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        combo.setFixedHeight(26)
        return combo

    # --- Events ---

    def get_resize_dir(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = 14  # grab margin
        
        on_left = x < m
        on_right = x > w - m
        on_top = y < m
        on_bottom = y > h - m
        
        if on_top and on_left: return 5
        if on_bottom and on_right: return 6
        if on_top and on_right: return 7
        if on_bottom and on_left: return 8
        if on_top: return 1
        if on_bottom: return 2
        if on_left: return 3
        if on_right: return 4
        return 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            local_pos = self.mapFromGlobal(event.globalPos())
            # Only allow dragging if the click is in the header region
            if self.header_frame.geometry().contains(local_pos):
                self._drag_active = True
                self.oldPos = event.globalPos()
                self._resize_dir = 0 # Not resizing if dragging from header
                event.accept()
            else:
                # Still allow resizing from edges
                self._resize_dir = self.get_resize_dir(local_pos)
                if self._resize_dir:
                    self._drag_active = True
                    self.oldPos = event.globalPos()
                    self._start_geometry = self.geometry()
                    event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if getattr(self, '_drag_active', False) and getattr(self, '_resize_dir', 0) != 0:
                try:
                    from settings_manager import SettingsManager
                    settings = SettingsManager()
                    settings.set("popup_size", [self.width(), self.height()])
                except Exception:
                    pass
            self._drag_active = False
            self._resize_dir = 0
            event.accept()

    def mouseMoveEvent(self, event):
        if getattr(self, '_drag_active', False) and (event.buttons() & Qt.LeftButton):
            gp = event.globalPos()
            dx = gp.x() - self.oldPos.x()
            dy = gp.y() - self.oldPos.y()
            if getattr(self, '_resize_dir', 0):
                g = self._start_geometry
                x, y, w, h = g.x(), g.y(), g.width(), g.height()
                mw, mh = 300, 300
                if self._resize_dir in [3, 5, 8]:  # left edges
                    nw = max(mw, g.width() - dx)
                    if nw > mw: x = g.x() + dx
                    w = nw
                elif self._resize_dir in [4, 6, 7]:  # right edges
                    w = max(mw, g.width() + dx)
                if self._resize_dir in [1, 5, 7]:  # top edges
                    nh = max(mh, g.height() - dy)
                    if nh > mh: y = g.y() + dy
                    h = nh
                elif self._resize_dir in [2, 6, 8]:  # bottom edges
                    h = max(mh, g.height() + dy)
                self.setGeometry(x, y, w, h)
            else:  # move
                self.move(self.x() + dx, self.y() + dy)
                self.oldPos = gp
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.active_command:
                self.clear_command_mode()
            else:
                self.close()

    def closeEvent(self, event):
        # Stop the cursor-polling timer so it doesn't fire after destruction
        if hasattr(self, '_cursor_timer') and self._cursor_timer:
            self._cursor_timer.stop()
            self._cursor_timer = None

        # Clean up any dynamic command-mode widgets
        for widget in getattr(self, 'dynamic_widgets', []):
            try:
                widget.deleteLater()
            except Exception:
                pass
        self.dynamic_widgets = []
        self.arg_fields = []

        # Clean up settings window if open
        if hasattr(self, 'settings_window') and self.settings_window:
            try:
                self.settings_window.close()
                self.settings_window.deleteLater()
            except Exception:
                pass
            self.settings_window = None

        try:
            import utils, win32gui
            if hasattr(utils, 'PREV_HWND') and utils.PREV_HWND:
                win32gui.SetForegroundWindow(utils.PREV_HWND)
        except: pass
        
        try:
            from settings_manager import SettingsManager
            settings = SettingsManager()
            settings.set("popup_size", [self.width(), self.height()])
        except Exception:
            pass
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backspace:
            if self.active_command and getattr(self, "arg_fields", None) and obj in self.arg_fields:
                idx = self.arg_fields.index(obj)
                if idx == 0 and not obj.text():
                    self.clear_command_mode()
                    return True
        if obj == getattr(self, "central_frame", None):
            if event.type() == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            elif event.type() == QEvent.MouseMove:
                self.mouseMoveEvent(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
        return super().eventFilter(obj, event)

    def open_settings(self):
        from settings_ui import SettingsWindow
        self.settings_window = SettingsWindow(parent=self)
        self.settings_window.show()
        
    def update_font_size(self, size):
        self.current_font_size = size
        for lbl in getattr(self, "message_labels", []):
            try:
                lbl.setStyleSheet(f"font-size: {size}px; color: {utils.THEME['text']}; background: transparent; selection-background-color: {utils.THEME['primary']};")
            except Exception:
                pass

    # --- Slash command logic ---

    def on_command_selected(self, cmd_text):
        # Prevent double-fire (completer + send_message both calling this)
        if self.active_command or self._ignoring_send:
            return
        
        self._ignoring_send = True
        
        if cmd_text in self.no_arg_commands:
            QTimer.singleShot(50, lambda: self._fire_no_arg(cmd_text))
            return
        
        fields = self.command_fields.get(cmd_text)
        if not fields:
            QTimer.singleShot(50, lambda: self._fire_no_arg(cmd_text))
            return
        
        self.active_command = cmd_text
        QTimer.singleShot(50, lambda: self._build_fields(cmd_text, fields))
    
    def _fire_no_arg(self, cmd_text):
        self.input_field.clear()
        self._ignoring_send = False
        self.append_message("You", cmd_text)
        self.user_message_sent.emit(cmd_text)
    
    def _build_fields(self, cmd_text, fields):
        self.input_field.clear()
        self.input_field.hide()
        self._ignoring_send = False
        
        # Add command chip (e.g. "move")
        chip = self._make_cmd_chip(cmd_text.lstrip("/"))
        self.wrapper_layout.insertWidget(0, chip)
        self.dynamic_widgets.append(chip)
        
        self.arg_fields = []
        
        for field_def in fields:
            if field_def["type"] == "label":
                lbl = self._make_label_chip(field_def["text"])
                self.wrapper_layout.addWidget(lbl)
                self.dynamic_widgets.append(lbl)
            elif field_def["type"] == "input":
                inp = self._make_arg_input(field_def["ph"])
                inp.installEventFilter(self)
                self.wrapper_layout.addWidget(inp)
                self.dynamic_widgets.append(inp)
                self.arg_fields.append(inp)
            elif field_def["type"] == "select":
                combo = self._make_arg_select(field_def["options"])
                combo.installEventFilter(self)
                self.wrapper_layout.addWidget(combo)
                self.dynamic_widgets.append(combo)
                self.arg_fields.append(combo)
        
        if self.arg_fields:
            self.arg_fields[0].setFocus()
    

    
    def clear_command_mode(self):
        for widget in self.dynamic_widgets:
            self.wrapper_layout.removeWidget(widget)
            widget.deleteLater()
        self.dynamic_widgets = []
        self.arg_fields = []
        self.active_command = None
        
        self.input_field.clear()
        self.input_field.setPlaceholderText("Type a command or /help...")
        self.input_field.show()
        self.input_field.setFocus()

    def on_text_changed(self, text):
        if not self.active_command:
            self.input_field.setPlaceholderText("Type a command or /help...")

    # --- Send ---

    def send_message(self):
        if self._ignoring_send:
            return
            
        if self.active_command:
            args = [(f.text() if hasattr(f, "text") else f.currentText()).strip() for f in self.arg_fields]
            full_text = f"{self.active_command} {' '.join(args)}".strip()
            self.clear_command_mode()
            if full_text:
                self.append_message("You", full_text)
                self.user_message_sent.emit(full_text)
        else:
            text = self.input_field.text().strip()
            if not text:
                return
            
            # If user typed an exact slash command (or completed one) and pressed Enter, 
            # show the fields instead of sending raw text
            clean_cmd = text.split(" - ")[0]
            all_cmds = list(self.command_fields.keys()) + self.no_arg_commands
            if clean_cmd in all_cmds:
                self.on_command_selected(clean_cmd)
                return
            
            self.append_message("You", text)
            self.input_field.clear()
            self.input_field.setPlaceholderText("Type a command or /help...")
            self.user_message_sent.emit(text)

    def append_message(self, sender, text):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 5, 0, 5)
        
        bubble = QFrame()
        bubble.setMinimumWidth(10)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        bubble_layout.setSpacing(4)
        
        name_lbl = QLabel(sender)
        
        url_to_copy = None
        if "[COPY_BTN:" in text:
            start = text.find("[COPY_BTN:") + len("[COPY_BTN:")
            end = text.find("]", start)
            if end != -1:
                url_to_copy = text[start:end]
                # Remove the tag from the text entirely
                text = text.replace(f"[COPY_BTN:{url_to_copy}]", "").strip()

        msg_lbl = QLabel(text.replace('\n', '<br>'))
        msg_lbl.setWordWrap(True)
        msg_lbl.setMinimumWidth(10)
        msg_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.TextSelectableByMouse)
        msg_lbl.setOpenExternalLinks(False)
        msg_lbl.linkActivated.connect(self._on_link_clicked)
        msg_lbl.setProperty("is_coral", sender == "Coral")
        
        bubble_layout.addWidget(name_lbl)
        bubble_layout.addWidget(msg_lbl)

        # Add the custom inline copy button if requested 
        if url_to_copy:
            btn_layout = QHBoxLayout()
            btn_copy = QPushButton("Copy URL")
            btn_copy.setCursor(Qt.PointingHandCursor)
            
            # Simple style for small bubble buttons
            btn_copy.setStyleSheet(f"""
                QPushButton {{
                    background: #2D2D44; color: #E0E0E0; border: 1px solid #444;
                    border-radius: 4px; padding: 4px 8px; font-size: 11px;
                }}
                QPushButton:hover {{
                    background: #3D3D54; border-color: {utils.THEME['primary']};
                }}
            """)
            btn_copy.clicked.connect(lambda _, url=url_to_copy: QApplication.clipboard().setText(url))
            btn_layout.addWidget(btn_copy)
            btn_layout.addStretch()
            bubble_layout.addLayout(btn_layout)
        
        # Add quick-action buttons if AI asks the common disambiguation question
        if sender == "Coral" and "Did you mean the app or the folder?" in text:
            btn_layout = QHBoxLayout()
            btn_app = QPushButton("App")
            btn_app.setCursor(Qt.PointingHandCursor)
            
            btn_folder = QPushButton("Folder")
            btn_folder.setCursor(Qt.PointingHandCursor)
            
            # Rich UI styling including disabled states
            style = f"""
                QPushButton {{
                    background: {utils.THEME['surface']}; color: #E0E0E0; border: 1px solid #555;
                    border-radius: 4px; padding: 6px 12px; font-weight: bold; font-size: 11px;
                }}
                QPushButton:hover {{
                    background: #3D3D54; border-color: {utils.THEME['primary']};
                }}
                QPushButton:disabled {{
                    background: #1A1A24; color: #555; border-color: #333;
                }}
            """
            btn_app.setStyleSheet(style)
            btn_folder.setStyleSheet(style)
            
            def handle_click(is_app=True, b1=btn_app, b2=btn_folder):
                b1.setEnabled(False)
                b2.setEnabled(False)
                if is_app:
                    self._simulate_user_message("I meant the application. Please open the app.")
                else:
                    self._simulate_user_message("I meant the folder. Please open the file directory.")

            btn_app.clicked.connect(lambda: handle_click(True, btn_app, btn_folder))
            btn_folder.clicked.connect(lambda: handle_click(False, btn_app, btn_folder))
            
            btn_layout.addWidget(btn_app)
            btn_layout.addWidget(btn_folder)
            bubble_layout.addLayout(btn_layout)

        if sender == "Coral":
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {utils.THEME['surface']};
                    border-radius: 12px;
                }}
            """)
            name_lbl.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {utils.THEME['primary']}; margin-bottom: 2px; background: transparent;")
            msg_lbl.setStyleSheet(f"font-size: {self.current_font_size}px; color: {utils.THEME['text']}; background: transparent; selection-background-color: {utils.THEME['primary']};")
            container_layout.addWidget(bubble, stretch=8)
            container_layout.addStretch(1)
        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {utils.THEME['surface']};
                    border-radius: 12px;
                }}
            """)
            name_lbl.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {utils.THEME['primary']}; margin-bottom: 2px; background: transparent;")
            msg_lbl.setStyleSheet(f"font-size: {self.current_font_size}px; color: {utils.THEME['text']}; background: transparent; selection-background-color: {utils.THEME['primary']};")
            container_layout.addStretch(1)
            container_layout.addWidget(bubble, stretch=8)
            
        self.message_labels.append(msg_lbl)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        
        QTimer.singleShot(50, lambda: self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum()))

    def _simulate_user_message(self, text):
        if not self.input_field.isEnabled(): return
        self.input_field.setText(text)
        QTimer.singleShot(0, self.send_message)
        
    def _on_link_clicked(self, url):
        import os
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        try:
            if url.startswith("file:///"):
                path = url.replace("file:///", "", 1)
                os.startfile(path)
            else:
                QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"Failed to open link: {e}")

    def set_loading(self, is_loading):
        if is_loading:
            self.input_field.setEnabled(False)
            for f in self.arg_fields:
                f.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.send_btn.setText("...")
        else:
            self.input_field.setEnabled(True)
            for f in self.arg_fields:
                f.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.send_btn.setText("Send")
            if self.arg_fields:
                self.arg_fields[0].setFocus()
            else:
                self.input_field.setFocus()
