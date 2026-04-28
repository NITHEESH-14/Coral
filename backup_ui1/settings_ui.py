from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QApplication, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
import utils
from settings_manager import SettingsManager


class ToggleSwitch(QWidget):
    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(42, 22)
        self.setCursor(Qt.PointingHandCursor)
        self._circle_pos = 22 if checked else 2
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, val):
        self._checked = val
        self._circle_pos = 22 if val else 2
        self.update()
    
    def mousePressEvent(self, event):
        self._checked = not self._checked
        start = self._circle_pos
        end = 22 if self._checked else 2
        self._animate(start, end)
    
    def _animate(self, start, end):
        import threading, time
        def run():
            steps = 6
            for i in range(steps + 1):
                self._circle_pos = start + (end - start) * i / steps
                self.update()
                time.sleep(0.015)
        threading.Thread(target=run, daemon=True).start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track_color = QColor(utils.THEME['primary']) if self._checked else QColor("#555")
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 42, 22, 11, 11)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(int(self._circle_pos), 2, 18, 18)
        painter.end()


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedSize(340, 290)
        
        screen = QApplication.desktop().screenGeometry()
        self.move(int((screen.width() - 340) / 2), int((screen.height() - 290) / 2))
        
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {utils.THEME['background']};
                color: {utils.THEME['text']};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet(f"color: {utils.THEME['primary']}; font-size: 15px; font-weight: bold;")
        close_btn = QPushButton("X")
        close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaa; font-weight: bold; padding: 0px; border: none; }
            QPushButton:hover { color: white; }
        """)
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Divider
        div1 = QFrame(); div1.setFrameShape(QFrame.HLine); div1.setStyleSheet("color: #444;")
        layout.addWidget(div1)
        
        # Toggle: Confirm actions
        row1 = QHBoxLayout()
        col1 = QVBoxLayout(); col1.setSpacing(1)
        lbl1 = QLabel("Confirm before actions")
        lbl1.setStyleSheet("font-size: 12px;")
        desc1 = QLabel("Ask before create, move, rename...")
        desc1.setStyleSheet("font-size: 10px; color: #777;")
        col1.addWidget(lbl1); col1.addWidget(desc1)
        self.toggle_actions = ToggleSwitch(self.settings.get("confirm_actions", True))
        row1.addLayout(col1); row1.addStretch(); row1.addWidget(self.toggle_actions)
        layout.addLayout(row1)
        
        # Toggle: Confirm deletes
        row2 = QHBoxLayout()
        col2 = QVBoxLayout(); col2.setSpacing(1)
        lbl2 = QLabel("Confirm before delete")
        lbl2.setStyleSheet("font-size: 12px;")
        desc2 = QLabel("Extra safety for destructive ops")
        desc2.setStyleSheet("font-size: 10px; color: #777;")
        col2.addWidget(lbl2); col2.addWidget(desc2)
        self.toggle_deletes = ToggleSwitch(self.settings.get("confirm_deletes", True))
        row2.addLayout(col2); row2.addStretch(); row2.addWidget(self.toggle_deletes)
        layout.addLayout(row2)
        
        # Info about apps
        div2 = QFrame(); div2.setFrameShape(QFrame.HLine); div2.setStyleSheet("color: #444;")
        layout.addWidget(div2)
        
        # Font Size
        font_row = QHBoxLayout()
        font_label = QLabel("Chat Font Size")
        font_label.setStyleSheet("font-size: 12px;")
        
        self.font_size = self.settings.get("base_font_size", 13)
        self.font_val_label = QLabel(str(self.font_size))
        self.font_val_label.setStyleSheet("font-size: 12px; font-weight: bold; color: white;")
        self.font_val_label.setAlignment(Qt.AlignCenter)
        self.font_val_label.setFixedWidth(20)
        
        btn_minus = QPushButton("-")
        btn_minus.setFixedSize(24, 24)
        btn_minus.setStyleSheet(f"background-color: {utils.THEME['surface']}; color: white; border-radius: 12px; font-weight: bold;")
        btn_minus.clicked.connect(lambda: self.change_font_size(-1))
        
        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(24, 24)
        btn_plus.setStyleSheet(f"background-color: {utils.THEME['surface']}; color: white; border-radius: 12px; font-weight: bold;")
        btn_plus.clicked.connect(lambda: self.change_font_size(1))
        
        font_row.addWidget(font_label)
        font_row.addStretch()
        font_row.addWidget(btn_minus)
        font_row.addWidget(self.font_val_label)
        font_row.addWidget(btn_plus)
        layout.addLayout(font_row)
        
        div3 = QFrame(); div3.setFrameShape(QFrame.HLine); div3.setStyleSheet("color: #444;")
        layout.addWidget(div3)
        
        app_note = QLabel("Apps are auto-discovered via Everything search.\nJust say 'open in [app name]' and Coral finds it.")
        app_note.setStyleSheet("font-size: 10px; color: #777; font-style: italic;")
        app_note.setWordWrap(True)
        layout.addWidget(app_note)
        
        layout.addStretch()
        
        # Save
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(90)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {utils.THEME['primary']};
                color: white; border: none; border-radius: 10px; padding: 7px 15px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #FF6633; }}
        """)
        save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)
        
        self.oldPos = self.pos()
        
    def change_font_size(self, delta):
        new_size = max(9, min(24, self.font_size + delta))
        self.font_size = new_size
        self.font_val_label.setText(str(self.font_size))
        
        if hasattr(self.parentWidget(), "update_font_size"):
            self.parentWidget().update_font_size(new_size)
        
    def save_and_close(self):
        self.settings.set("confirm_actions", self.toggle_actions.isChecked())
        self.settings.set("confirm_deletes", self.toggle_deletes.isChecked())
        self.settings.set("base_font_size", self.font_size)
        self.close()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
