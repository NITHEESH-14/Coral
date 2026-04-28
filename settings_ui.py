from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QApplication, QFrame, QScrollArea, QLineEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
import utils
from settings_manager import SettingsManager


class ToggleSwitch(QWidget):
    def __init__(self, checked=True, parent=None, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self._checked = checked
        self.setFixedSize(46, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._circle_pos = 24 if checked else 2
        from PyQt5.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._anim_step)
        self._anim_steps = 10
        self._anim_current = 0
        self._anim_start = 0
        self._anim_end = 0
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, val):
        self._checked = val
        self._circle_pos = 24 if val else 2
        self.update()
    
    def mousePressEvent(self, event):
        self._checked = not self._checked
        if self.on_change:
            self.on_change()
        start = self._circle_pos
        end = 24 if self._checked else 2
        self._animate(start, end)
    
    def _animate(self, start, end):
        self._anim_start = start
        self._anim_end = end
        self._anim_current = 0
        self._timer.start(10)
    
    def _anim_step(self):
        self._anim_current += 1
        self._circle_pos = self._anim_start + (self._anim_end - self._anim_start) * (self._anim_current / self._anim_steps)
        self.update()
        if self._anim_current >= self._anim_steps:
            self._timer.stop()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track_color = QColor(utils.THEME['primary']) if self._checked else QColor("#555")
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 46, 24, 12, 12)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(int(self._circle_pos), 2, 20, 20)
        painter.end()


class HotkeyInput(QLineEdit):
    def __init__(self, default_val, parent=None):
        super().__init__(default_val, parent)
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return super().keyPressEvent(event)
            
        parts = []
        if modifiers & Qt.ControlModifier: parts.append("<ctrl>")
        if modifiers & Qt.AltModifier: parts.append("<alt>")
        if modifiers & Qt.ShiftModifier: parts.append("<shift>")
        if modifiers & Qt.MetaModifier: parts.append("<cmd>")
        
        key_text = ""
        if Qt.Key_A <= key <= Qt.Key_Z:
            key_text = chr(key).lower()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            key_text = chr(key)
        else:
            mapping = {
                Qt.Key_Space: "<space>", Qt.Key_Return: "<enter>", Qt.Key_Enter: "<enter>",
                Qt.Key_Escape: "<esc>", Qt.Key_Tab: "<tab>", Qt.Key_Up: "<up>",
                Qt.Key_Down: "<down>", Qt.Key_Left: "<left>", Qt.Key_Right: "<right>",
            }
            for i in range(1, 13): mapping[getattr(Qt, f"Key_F{i}")] = f"<f{i}>"
            key_text = mapping.get(key, "")
            
            if not key_text:
                if event.text():
                    key_text = event.text().strip().lower()

        if key_text:
            parts.append(key_text)
            self.setText("+".join(parts))
            if hasattr(self.window(), "save_settings"):
                self.window().save_settings()
        else:
            return super().keyPressEvent(event)


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        saved_size = self.settings.get("settings_size", [340, 290])
        w = max(300, saved_size[0])
        h = max(290, saved_size[1])
        self.resize(w, h)
        
        screen = QApplication.desktop().screenGeometry()
        self.move(int((screen.width() - w) / 2), int((screen.height() - h) / 2))
        self.setObjectName("SettingsWindowObj")
        
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget#SettingsWindowObj {{
                background-color: rgba(1, 1, 1, 1);
            }}
            QFrame#SettingsFrame {{
                background-color: {utils.THEME['background']};
                border-radius: 16px;
                border: 1px solid #444;
            }}
            QWidget {{
                color: {utils.THEME['text']};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
        """)
        
        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("SettingsFrame")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.central_frame)
        
        frame_layout = QVBoxLayout(self.central_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(10)

        # Header Fixed
        header_layout = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet(f"color: {utils.THEME['primary']}; font-size: 16px; font-weight: bold;")
        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {utils.THEME['primary']}; font-weight: bold; padding: 0px; font-size: 14px; border: none; border-radius: 13px; }}
            QPushButton:hover {{ color: white; background-color: #444; }}
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        frame_layout.addLayout(header_layout)
        
        div_header = QFrame(); div_header.setFrameShape(QFrame.HLine); div_header.setStyleSheet("color: #444;")
        frame_layout.addWidget(div_header)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
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

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        scroll.setWidget(container)
        
        frame_layout.addWidget(scroll)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 15, 5) # Leave room for scrollbar 
        layout.setSpacing(16)
        
        self.font_size = self.settings.get("base_font_size", 13)
        lbl_size = max(10, self.font_size - 1)
        tiny_size = max(9, self.font_size - 2)

        # Toggle: Confirm actions
        row1 = QHBoxLayout()
        col1 = QVBoxLayout(); col1.setSpacing(2)
        self.lbl1 = QLabel("Confirm before actions")
        self.lbl1.setStyleSheet(f"font-size: {lbl_size}px;")

        self.desc1 = QLabel("Ask before create, move, rename...")
        self.desc1.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        col1.addWidget(self.lbl1); col1.addWidget(self.desc1)
        self.toggle_actions = ToggleSwitch(self.settings.get("confirm_actions", True), on_change=self.save_settings)
        row1.addLayout(col1); row1.addStretch(); row1.addWidget(self.toggle_actions)
        layout.addLayout(row1)
        
        # Toggle: Confirm deletes
        row2 = QHBoxLayout()
        col2 = QVBoxLayout(); col2.setSpacing(2)
        self.lbl2 = QLabel("Confirm before delete")
        self.lbl2.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc2 = QLabel("Extra safety for destructive ops")
        self.desc2.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        col2.addWidget(self.lbl2); col2.addWidget(self.desc2)
        self.toggle_deletes = ToggleSwitch(self.settings.get("confirm_deletes", True), on_change=self.save_settings)
        row2.addLayout(col2); row2.addStretch(); row2.addWidget(self.toggle_deletes)
        layout.addLayout(row2)
        
        # Divider
        div2 = QFrame(); div2.setFrameShape(QFrame.HLine); div2.setStyleSheet("color: #444;")
        layout.addWidget(div2)
        
        # Font Size
        font_row = QHBoxLayout()
        self.font_label = QLabel("Chat Font Size")
        self.font_label.setStyleSheet(f"font-size: {lbl_size}px;")
        self.font_val_label = QLabel(str(self.font_size))
        self.font_val_label.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        self.font_val_label.setAlignment(Qt.AlignCenter)
        self.font_val_label.setFixedWidth(24)
        
        btn_minus = QPushButton("-")
        btn_minus.setFixedSize(26, 26)
        btn_minus.setCursor(Qt.PointingHandCursor)
        btn_minus.setStyleSheet(f"background-color: #444; color: white; border-radius: 13px; font-weight: bold; font-size: 14px;")
        btn_minus.clicked.connect(lambda: self.change_font_size(-1))
        
        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(26, 26)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setStyleSheet(f"background-color: #444; color: white; border-radius: 13px; font-weight: bold; font-size: 14px;")
        btn_plus.clicked.connect(lambda: self.change_font_size(1))
        
        font_row.addWidget(self.font_label)
        font_row.addStretch()
        font_row.addWidget(btn_minus)
        font_row.addWidget(self.font_val_label)
        font_row.addWidget(btn_plus)
        layout.addLayout(font_row)

        div3 = QFrame(); div3.setFrameShape(QFrame.HLine); div3.setStyleSheet("color: #444;")
        layout.addWidget(div3)

        # ── QR/Link Auto-Actions ──────────────────────────────────
        row_qr1 = QHBoxLayout()
        col_qr1 = QVBoxLayout(); col_qr1.setSpacing(2)
        self.lbl_qr1 = QLabel("Open QR URLs in browser")
        self.lbl_qr1.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc_qr1 = QLabel("Automatically launch browser on detection")
        self.desc_qr1.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        col_qr1.addWidget(self.lbl_qr1); col_qr1.addWidget(self.desc_qr1)
        self.toggle_qr_open = ToggleSwitch(self.settings.get("qr_open_browser", False), on_change=self.save_settings)
        row_qr1.addLayout(col_qr1); row_qr1.addStretch(); row_qr1.addWidget(self.toggle_qr_open)
        layout.addLayout(row_qr1)

        row_qr2 = QHBoxLayout()
        col_qr2 = QVBoxLayout(); col_qr2.setSpacing(2)
        self.lbl_qr2 = QLabel("Copy QR data to clipboard")
        self.lbl_qr2.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc_qr2 = QLabel("Automatically copy detected text/URLs")
        self.desc_qr2.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        col_qr2.addWidget(self.lbl_qr2); col_qr2.addWidget(self.desc_qr2)
        self.toggle_qr_copy = ToggleSwitch(self.settings.get("qr_copy_clipboard", False), on_change=self.save_settings)
        row_qr2.addLayout(col_qr2); row_qr2.addStretch(); row_qr2.addWidget(self.toggle_qr_copy)
        layout.addLayout(row_qr2)

        div_qr = QFrame(); div_qr.setFrameShape(QFrame.HLine); div_qr.setStyleSheet("color: #444;")
        layout.addWidget(div_qr)

        # ── Vault Auto-Cleanup ───────────────────────────────────
        self.vault_days = self.settings.get("vault_cleanup_days", 7)
        vault_row = QHBoxLayout()
        vault_col = QVBoxLayout(); vault_col.setSpacing(2)
        self.vault_lbl = QLabel("Vault Auto-Cleanup")
        self.vault_lbl.setStyleSheet(f"font-size: {lbl_size}px;")
        self.vault_desc = QLabel("Delete entries older than N days (0 = never)")
        self.vault_desc.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        vault_col.addWidget(self.vault_lbl)
        vault_col.addWidget(self.vault_desc)

        self.vault_val_label = QLabel("Never" if self.vault_days == 0 else f"{self.vault_days}d")
        self.vault_val_label.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        self.vault_val_label.setAlignment(Qt.AlignCenter)
        self.vault_val_label.setFixedWidth(42)

        vault_minus = QPushButton("-")
        vault_minus.setFixedSize(26, 26)
        vault_minus.setCursor(Qt.PointingHandCursor)
        vault_minus.setStyleSheet(f"background-color: #444; color: white; border-radius: 13px; font-weight: bold; font-size: 14px;")
        vault_minus.clicked.connect(lambda: self.change_vault_days(-1))

        vault_plus = QPushButton("+")
        vault_plus.setFixedSize(26, 26)
        vault_plus.setCursor(Qt.PointingHandCursor)
        vault_plus.setStyleSheet(f"background-color: #444; color: white; border-radius: 13px; font-weight: bold; font-size: 14px;")
        vault_plus.clicked.connect(lambda: self.change_vault_days(1))

        vault_row.addLayout(vault_col)
        vault_row.addStretch()
        vault_row.addWidget(vault_minus)
        vault_row.addWidget(self.vault_val_label)
        vault_row.addWidget(vault_plus)
        layout.addLayout(vault_row)
        # ──────────────────────────────────────────────
        
        self.app_note = QLabel("Apps are auto-discovered via Everything search.\nJust say 'open in [app name]' and Coral finds it.")
        self.app_note.setStyleSheet(f"font-size: {tiny_size}px; color: #777; font-style: italic;")
        self.app_note.setWordWrap(True)
        layout.addWidget(self.app_note)

        div4 = QFrame(); div4.setFrameShape(QFrame.HLine); div4.setStyleSheet("color: #444;")
        layout.addWidget(div4)

        # ── Global Hotkeys ───────────────────────────────────────
        self.hk_header = QLabel("Global Hotkeys")
        self.hk_header.setStyleSheet(f"font-size: {lbl_size + 2}px; font-weight: bold; color: {utils.THEME['primary']};")
        layout.addWidget(self.hk_header)

        # Helper method for creating hotkey input fields
        def make_hk_input(default_val):
            inp = HotkeyInput(default_val)
            inp.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #333; color: white; border: 1px solid #555; 
                    border-radius: 6px; padding: 4px; font-family: monospace; font-size: 13px; font-weight: bold;
                }}
                QLineEdit:focus {{ border: 1px solid {utils.THEME['primary']}; }}
            """)
            inp.setFixedWidth(140)
            return inp

        row_hk_snip = QHBoxLayout()
        self.lbl_hk_snip = QLabel("Capture Suite Hotkey"); self.lbl_hk_snip.setStyleSheet(f"font-size: {lbl_size}px;")
        self.hk_snip_input = make_hk_input(self.settings.get("hotkey_snip", "<ctrl>+<shift>+s"))
        row_hk_snip.addWidget(self.lbl_hk_snip); row_hk_snip.addStretch(); row_hk_snip.addWidget(self.hk_snip_input)
        layout.addLayout(row_hk_snip)

        row_hk_global = QHBoxLayout()
        self.lbl_hk_global = QLabel("Command Center Hotkey"); self.lbl_hk_global.setStyleSheet(f"font-size: {lbl_size}px;")
        self.hk_global_input = make_hk_input(self.settings.get("hotkey_global", "<ctrl>+<shift>+g"))
        row_hk_global.addWidget(self.lbl_hk_global); row_hk_global.addStretch(); row_hk_global.addWidget(self.hk_global_input)
        layout.addLayout(row_hk_global)

        row_hk_rec = QHBoxLayout()
        self.lbl_hk_rec = QLabel("Screen Recorder Hotkey"); self.lbl_hk_rec.setStyleSheet(f"font-size: {lbl_size}px;")
        self.hk_rec_input = make_hk_input(self.settings.get("hotkey_record", "<ctrl>+<shift>+x"))
        row_hk_rec.addWidget(self.lbl_hk_rec); row_hk_rec.addStretch(); row_hk_rec.addWidget(self.hk_rec_input)
        layout.addLayout(row_hk_rec)

        self.hk_note = QLabel("Click a field and press your key combination. Requires app restart to apply.")
        self.hk_note.setStyleSheet(f"font-size: {tiny_size + 1}px; color: #777; font-style: italic;")
        self.hk_note.setWordWrap(True)
        layout.addWidget(self.hk_note)

        div_hk = QFrame(); div_hk.setFrameShape(QFrame.HLine); div_hk.setStyleSheet("color: #444;")
        layout.addWidget(div_hk)

        # ── AI Model Provider ───────────────────────────────────
        model_row = QHBoxLayout()
        model_col = QVBoxLayout(); model_col.setSpacing(2)
        model_lbl = QLabel("Intelligence Provider")
        model_lbl.setStyleSheet(f"font-size: {lbl_size}px;")
        model_desc = QLabel("Gemini adds native vision; Groq is faster")
        model_desc.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        model_col.addWidget(model_lbl); model_col.addWidget(model_desc)
        
        self.prov_btn = QPushButton(self.settings.get("model_provider", "Groq"))
        self.prov_btn.setFixedWidth(120)
        self.prov_btn.setCursor(Qt.PointingHandCursor)
        self.prov_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #333; color: {utils.THEME['primary']}; 
                border: 1px solid #555; border-radius: 6px; 
                padding: 4px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #444; }}
        """)
        def toggle_prov():
            curr = self.prov_btn.text()
            new_p = "Gemini" if curr == "Groq" else "Groq"
            self.prov_btn.setText(new_p)
            self.save_settings()
        self.prov_btn.clicked.connect(toggle_prov)
        
        model_row.addLayout(model_col)
        model_row.addStretch()
        model_row.addWidget(self.prov_btn)
        layout.addLayout(model_row)

        # ── Specific Model Selection ──────────────────────────────
        self.spec_model_row = QHBoxLayout()
        spec_model_col = QVBoxLayout(); spec_model_col.setSpacing(2)
        spec_model_lbl = QLabel("Model Selection")
        spec_model_lbl.setStyleSheet(f"font-size: {lbl_size}px;")
        self.spec_model_desc = QLabel("Choose the specific brain version")
        self.spec_model_desc.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        spec_model_col.addWidget(spec_model_lbl); spec_model_col.addWidget(self.spec_model_desc)

        self.model_btn = QPushButton()
        self.model_btn.setFixedWidth(150)
        self.model_btn.setCursor(Qt.PointingHandCursor)
        self.model_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #333; color: {utils.THEME['primary']}; 
                border: 1px solid #555; border-radius: 6px; 
                padding: 4px; font-weight: bold; font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #444; }}
        """)
        
        def update_models():
            if self.prov_btn.text() == "Gemini":
                saved = self.settings.get("gemini_model", "gemini-2.0-flash")
            else:
                saved = self.settings.get("groq_model", "llama-3.3-70b-versatile")
            self.model_btn.setText(saved)

        def cycle_model():
            curr = self.model_btn.text()
            if self.prov_btn.text() == "Gemini":
                options = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"]
            else:
                options = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
            
            try:
                idx = (options.index(curr) + 1) % len(options)
            except ValueError:
                idx = 0
            self.model_btn.setText(options[idx])
            self.save_settings()

        update_models()
        self.prov_btn.clicked.connect(update_models)
        self.model_btn.clicked.connect(cycle_model)

        self.spec_model_row.addLayout(spec_model_col)
        self.spec_model_row.addStretch()
        self.spec_model_row.addWidget(self.model_btn)
        layout.addLayout(self.spec_model_row)

        div5 = QFrame(); div5.setFrameShape(QFrame.HLine); div5.setStyleSheet("color: #444;")
        layout.addWidget(div5)
        # ── Macro Settings ──────────────────────────────────────────
        macro_header = QLabel("⏺  Macro Recorder")
        macro_header.setStyleSheet(f"font-size: {lbl_size}px; font-weight: bold; color: {utils.THEME['primary']};")
        self.macro_header = macro_header
        layout.addWidget(macro_header)

        # Toggle: Confirm before macro playback
        row_macro1 = QHBoxLayout()
        col_macro1 = QVBoxLayout(); col_macro1.setSpacing(2)
        self.lbl_macro1 = QLabel("Confirm before playback")
        self.lbl_macro1.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc_macro1 = QLabel("Ask before running a recorded macro")
        self.desc_macro1.setStyleSheet(f"font-size: {tiny_size}px; color: #777;")
        col_macro1.addWidget(self.lbl_macro1); col_macro1.addWidget(self.desc_macro1)
        self.toggle_macro_confirm = ToggleSwitch(self.settings.get("confirm_macro_play", True), on_change=self.save_settings)
        row_macro1.addLayout(col_macro1); row_macro1.addStretch(); row_macro1.addWidget(self.toggle_macro_confirm)
        layout.addLayout(row_macro1)

        # Toggle: Show macro toast notifications
        row_macro2 = QHBoxLayout()
        col_macro2 = QVBoxLayout(); col_macro2.setSpacing(2)
        self.lbl_macro2 = QLabel("Macro notifications")
        self.lbl_macro2.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc_macro2 = QLabel("Show status when macro starts / finishes")
        self.desc_macro2.setStyleSheet(f"font-size: {tiny_size}px; color: #777;")
        col_macro2.addWidget(self.lbl_macro2); col_macro2.addWidget(self.desc_macro2)
        self.toggle_macro_notify = ToggleSwitch(self.settings.get("macro_notify", True), on_change=self.save_settings)
        row_macro2.addLayout(col_macro2); row_macro2.addStretch(); row_macro2.addWidget(self.toggle_macro_notify)
        layout.addLayout(row_macro2)

        # Macro repeat count stepper
        macro_rep_row = QHBoxLayout()
        macro_rep_col = QVBoxLayout(); macro_rep_col.setSpacing(2)
        self.lbl_macro_rep = QLabel("Default repeat count")
        self.lbl_macro_rep.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc_macro_rep = QLabel("How many times to replay a macro")
        self.desc_macro_rep.setStyleSheet(f"font-size: {tiny_size}px; color: #777;")
        macro_rep_col.addWidget(self.lbl_macro_rep); macro_rep_col.addWidget(self.desc_macro_rep)

        self.macro_repeat = self.settings.get("macro_repeat", 1)
        self.macro_rep_val = QLabel(str(self.macro_repeat))
        self.macro_rep_val.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        self.macro_rep_val.setAlignment(Qt.AlignCenter)
        self.macro_rep_val.setFixedWidth(28)

        macro_rep_minus = QPushButton("-")
        macro_rep_minus.setFixedSize(26, 26)
        macro_rep_minus.setCursor(Qt.PointingHandCursor)
        macro_rep_minus.setStyleSheet(f"background-color: #444; color: white; border-radius: 13px; font-weight: bold; font-size: 14px;")
        macro_rep_minus.clicked.connect(lambda: self.change_macro_repeat(-1))

        macro_rep_plus = QPushButton("+")
        macro_rep_plus.setFixedSize(26, 26)
        macro_rep_plus.setCursor(Qt.PointingHandCursor)
        macro_rep_plus.setStyleSheet(f"background-color: #444; color: white; border-radius: 13px; font-weight: bold; font-size: 14px;")
        macro_rep_plus.clicked.connect(lambda: self.change_macro_repeat(1))

        macro_rep_row.addLayout(macro_rep_col)
        macro_rep_row.addStretch()
        macro_rep_row.addWidget(macro_rep_minus)
        macro_rep_row.addWidget(self.macro_rep_val)
        macro_rep_row.addWidget(macro_rep_plus)
        layout.addLayout(macro_rep_row)
        # ────────────────────────────────────────────────────────────
        
        layout.addStretch()
        
        # Refresh
        refresh_btn = QPushButton("Refresh App")
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setFixedHeight(32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {utils.THEME['primary']};
                color: white; border: none; border-radius: 16px; font-weight: bold; font-size: 13px;
                padding: 0px 20px;
            }}
            QPushButton:hover {{ background-color: #FF6633; }}
        """)
        refresh_btn.clicked.connect(self.restart_app)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        
        frame_layout.addLayout(btn_layout)
        
        self.oldPos = self.pos()
        self.setMouseTracking(True)
        self.central_frame.setMouseTracking(True)
        self.central_frame.installEventFilter(self)
        
        from PyQt5.QtCore import QTimer
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._update_cursor)
        self._cursor_timer.start(50)
        
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
        
    def restart_app(self):
        import sys, os, subprocess
        self.save_settings()
        subprocess.Popen([sys.executable] + sys.argv)
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()
        os._exit(0)

    def change_vault_days(self, delta):
        # Steps: 0, 1, 3, 7, 14, 30, 60, 90
        steps = [0, 1, 3, 7, 14, 30, 60, 90]
        try:
            idx = steps.index(self.vault_days)
        except ValueError:
            idx = steps.index(7)
        idx = max(0, min(len(steps) - 1, idx + delta))
        self.vault_days = steps[idx]
        self.vault_val_label.setText("Never" if self.vault_days == 0 else f"{self.vault_days}d")
        self.save_settings()

    def change_font_size(self, delta):
        new_size = max(9, min(24, self.font_size + delta))
        self.font_size = new_size
        self.font_val_label.setText(str(self.font_size))

        lbl_size = max(10, new_size - 1)
        tiny_size = max(9, new_size - 2)

        # Main labels
        self.lbl1.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl2.setStyleSheet(f"font-size: {lbl_size}px;")
        self.font_label.setStyleSheet(f"font-size: {lbl_size}px;")
        self.vault_lbl.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl_qr1.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl_qr2.setStyleSheet(f"font-size: {lbl_size}px;")
        # Descriptions
        self.desc1.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.desc2.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.desc_qr1.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.desc_qr2.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.vault_desc.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.app_note.setStyleSheet(f"font-size: {tiny_size}px; color: #888; font-style: italic;")
        
        # Hotkeys
        self.hk_header.setStyleSheet(f"font-size: {lbl_size + 2}px; font-weight: bold; color: {utils.THEME['primary']};")
        self.lbl_hk_snip.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl_hk_global.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl_hk_rec.setStyleSheet(f"font-size: {lbl_size}px;")
        self.hk_note.setStyleSheet(f"font-size: {tiny_size + 1}px; color: #777; font-style: italic;")
        
        # Macro labels
        self.macro_header.setStyleSheet(f"font-size: {lbl_size}px; font-weight: bold; color: {utils.THEME['primary']};")
        self.lbl_macro1.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl_macro2.setStyleSheet(f"font-size: {lbl_size}px;")
        self.lbl_macro_rep.setStyleSheet(f"font-size: {lbl_size}px;")
        self.desc_macro1.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.desc_macro2.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")
        self.desc_macro_rep.setStyleSheet(f"font-size: {tiny_size}px; color: #888;")

        if hasattr(self.parentWidget(), "update_font_size"):
            self.parentWidget().update_font_size(new_size)
            
        self.save_settings()
        
    def change_macro_repeat(self, delta):
        self.macro_repeat = max(1, min(20, self.macro_repeat + delta))
        self.macro_rep_val.setText(str(self.macro_repeat))
        self.save_settings()

    def save_settings(self):
        try:
            self.settings.set("confirm_actions", self.toggle_actions.isChecked())
            self.settings.set("confirm_deletes", self.toggle_deletes.isChecked())
            self.settings.set("base_font_size", self.font_size)
            self.settings.set("vault_cleanup_days", self.vault_days)
            self.settings.set("qr_open_browser", self.toggle_qr_open.isChecked())
            self.settings.set("qr_copy_clipboard", self.toggle_qr_copy.isChecked())
            self.settings.set("confirm_macro_play", self.toggle_macro_confirm.isChecked())
            self.settings.set("macro_notify", self.toggle_macro_notify.isChecked())
            self.settings.set("macro_repeat", self.macro_repeat)
            self.settings.set("model_provider", self.prov_btn.text())
            if self.prov_btn.text() == "Gemini":
                self.settings.set("gemini_model", self.model_btn.text())
            else:
                self.settings.set("groq_model", self.model_btn.text())
            
            # Hotkeys
            self.settings.set("hotkey_snip", self.hk_snip_input.text().strip().lower())
            self.settings.set("hotkey_global", self.hk_global_input.text().strip().lower())
            self.settings.set("hotkey_record", self.hk_rec_input.text().strip().lower())
            
            self.settings.set("settings_size", [self.width(), self.height()])
        except Exception:
            pass

    def closeEvent(self, event):
        # Stop the cursor-polling timer to avoid firing after destruction
        if hasattr(self, '_cursor_timer') and self._cursor_timer:
            self._cursor_timer.stop()
            self._cursor_timer = None
        self.save_settings()
        super().closeEvent(event)
        
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
            self._drag_active = True
            self.oldPos = event.globalPos()
            local_pos = self.mapFromGlobal(event.globalPos())
            self._resize_dir = self.get_resize_dir(local_pos)
            self._start_geometry = self.geometry()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if getattr(self, '_drag_active', False) and getattr(self, '_resize_dir', 0) != 0:
                self.save_settings()
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
                mw, mh = 200, 200
                if self._resize_dir in [3, 5, 8]:
                    nw = max(mw, g.width() - dx)
                    if nw > mw: x = g.x() + dx
                    w = nw
                elif self._resize_dir in [4, 6, 7]:
                    w = max(mw, g.width() + dx)
                if self._resize_dir in [1, 5, 7]:
                    nh = max(mh, g.height() - dy)
                    if nh > mh: y = g.y() + dy
                    h = nh
                elif self._resize_dir in [2, 6, 8]:
                    h = max(mh, g.height() + dy)
                self.setGeometry(x, y, w, h)
            else:
                self.move(self.x() + dx, self.y() + dy)
                self.oldPos = gp
            event.accept()

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
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
