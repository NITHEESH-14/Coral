from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QScrollArea, QFrame, QApplication, QCompleter, QSizeGrip
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
        
        popup_width = 350
        popup_height = 450
        
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
        
        self.init_ui()

    def init_ui(self):
        from settings_manager import SettingsManager
        settings = SettingsManager()
        font_size = settings.get("base_font_size", 13)
        
        # Main layout
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {utils.THEME['background']};
                color: {utils.THEME['text']};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            QTextEdit {{
                background-color: {utils.THEME['surface']};
                border: None;
                border-radius: 8px;
                padding: 10px;
                font-size: {font_size}px;
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
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. Header (Brand + Settings + Close)
        header_layout = QHBoxLayout()
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
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaa; font-weight: bold; padding: 0px; }
            QPushButton:hover { color: white; background-color: #444; border-radius: 15px; }
        """)
        close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        header_layout.addWidget(close_btn)
        
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

        # 3. Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
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
            "/create_folder": [{"type": "input", "ph": "folder name"}],
            "/create_file":   [{"type": "input", "ph": "file name"}],
            "/delete":        [{"type": "input", "ph": "file or folder"}],
            "/copy":          [{"type": "input", "ph": "file"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "destination"}],
            "/duplicate":     [{"type": "input", "ph": "file name"}],
            "/move":          [{"type": "input", "ph": "file"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "destination"}],
            "/rename":        [{"type": "input", "ph": "old name"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "new name"}],
            "/open":          [{"type": "input", "ph": "folder name"}],
            "/tag":           [{"type": "input", "ph": "file"}, {"type": "label", "text": "as"}, {"type": "input", "ph": "tag"}],
            "/untag":         [{"type": "input", "ph": "file"}, {"type": "label", "text": "remove"}, {"type": "input", "ph": "tag"}],
            "/convert":       [{"type": "input", "ph": "file"}, {"type": "label", "text": "to"}, {"type": "input", "ph": "format"}],
            "/shortcut":      [{"type": "input", "ph": "target file"}],
            "/info":          [{"type": "input", "ph": "file name"}],
            "/search_tag":    [{"type": "input", "ph": "tag name"}],
            "/bulk_rename":   [{"type": "input", "ph": "prefix"}],
        }
        
        self.no_arg_commands = ["/arrange", "/flatten", "/clean", "/usage", "/duplicates", "/tags", "/undo", "/help"]
        
        commands = [
            "/create_folder", "/create_file", "/delete", "/copy", "/duplicate", "/move", "/rename",
            "/open", "/arrange", "/flatten", "/clean", "/shortcut",
            "/info", "/usage", "/duplicates",
            "/tag", "/untag", "/search_tag", "/tags",
            "/convert", "/bulk_rename", "/undo", "/help"
        ]
        self.completer = QCompleter(commands, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchStartsWith)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        
        self.completer.popup().setStyleSheet(f"""
            QListView {{
                background-color: {utils.THEME['surface']};
                color: {utils.THEME['text']};
                border: 1px solid {utils.THEME['primary']};
                border-radius: 5px; padding: 4px; font-size: 13px;
            }}
            QListView::item {{ padding: 6px 10px; }}
            QListView::item:selected {{ background-color: {utils.THEME['primary']}; color: white; border-radius: 3px; }}
            QListView::item:hover {{ background-color: #444; }}
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
        # Apply padding so edges can be grabbed
        layout.setContentsMargins(6, 6, 6, 6)

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

    # --- Events ---

    def get_resize_dir(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = 10  # grab margin
        
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
            self.oldPos = event.globalPos()
            self._resize_dir = self.get_resize_dir(event.pos())
            self._start_geometry = self.geometry()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if getattr(self, "_resize_dir", 0) != 0:
                geom = self._start_geometry
                dx = event.globalPos().x() - self.oldPos.x()
                dy = event.globalPos().y() - self.oldPos.y()
                
                x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
                min_width, min_height = 300, 300
                
                if self._resize_dir in [3, 5, 8]: # left borders
                    w = max(min_width, geom.width() - dx)
                    if w > min_width: x = geom.x() + dx
                elif self._resize_dir in [4, 6, 7]: # right borders
                    w = max(min_width, geom.width() + dx)
                    
                if self._resize_dir in [1, 5, 7]: # top borders
                    h = max(min_height, geom.height() - dy)
                    if h > min_height: y = geom.y() + dy
                elif self._resize_dir in [2, 6, 8]: # bottom borders
                    h = max(min_height, geom.height() + dy)
                    
                self.setGeometry(x, y, w, h)
            else: # move window
                delta = event.globalPos() - self.oldPos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.oldPos = event.globalPos()
        else: # Update hover cursor
            r_dir = self.get_resize_dir(event.pos())
            if r_dir in [1, 2]: self.setCursor(Qt.SizeVerCursor)
            elif r_dir in [3, 4]: self.setCursor(Qt.SizeHorCursor)
            elif r_dir in [5, 6]: self.setCursor(Qt.SizeFDiagCursor)
            elif r_dir in [7, 8]: self.setCursor(Qt.SizeBDiagCursor)
            else: self.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.active_command:
                self.clear_command_mode()
            else:
                self.close()

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backspace:
            if self.active_command and obj in self.arg_fields:
                idx = self.arg_fields.index(obj)
                if idx == 0 and not obj.text():
                    self.clear_command_mode()
                    return True
        return super().eventFilter(obj, event)

    def open_settings(self):
        from settings_ui import SettingsWindow
        self.settings_window = SettingsWindow(parent=self)
        self.settings_window.show()
        
    def update_font_size(self, size):
        self.chat_history.setStyleSheet(f"""
            QTextEdit {{
                background-color: {utils.THEME['surface']};
                border: None;
                border-radius: 8px;
                padding: 10px;
                font-size: {size}px;
            }}
        """)

    # --- Slash command logic ---

    def on_command_selected(self, cmd_text):
        # Prevent double-fire (completer + send_message both calling this)
        if self.active_command:
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
            args = [f.text().strip() for f in self.arg_fields]
            full_text = f"{self.active_command} {' '.join(args)}".strip()
            self.clear_command_mode()
            if full_text:
                self.append_message("You", full_text)
                self.user_message_sent.emit(full_text)
        else:
            text = self.input_field.text().strip()
            if not text:
                return
            
            # If user typed an exact slash command and pressed Enter, 
            # show the fields instead of sending raw text
            all_cmds = list(self.command_fields.keys()) + self.no_arg_commands
            if text in all_cmds:
                self.on_command_selected(text)
                return
            
            self.append_message("You", text)
            self.input_field.clear()
            self.input_field.setPlaceholderText("Type a command or /help...")
            self.user_message_sent.emit(text)

    def append_message(self, sender, text):
        color = utils.THEME['primary'] if sender == "Coral" else "#B0C4DE"
        self.chat_history.append(f"<b style='color: {color}'>{sender}:</b> {text}<br>")
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
        
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
