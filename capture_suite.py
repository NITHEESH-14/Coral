import sys
import math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from io import BytesIO
from PIL import Image
from executor import ActionExecutor
from PyQt5.QtSvg import QSvgRenderer
import utils

# ─── SVG icon library ──────────────────────────────────────────────────────────
SVG_ICONS = {
    "ocr":        '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>''',
    "qr":         '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect><rect x="5" y="5" width="3" height="3" fill="#FFFFFF"></rect><rect x="16" y="5" width="3" height="3" fill="#FFFFFF"></rect><rect x="16" y="16" width="3" height="3" fill="#FFFFFF"></rect><rect x="5" y="16" width="3" height="3" fill="#FFFFFF"></rect></svg>''',
    "colors":     '''<svg viewBox="0 0 24 24" fill="none"><circle cx="8" cy="8" r="3" fill="#FF6B6B"></circle><circle cx="16" cy="8" r="3" fill="#FFD93D"></circle><circle cx="8" cy="16" r="3" fill="#6BCB77"></circle><circle cx="16" cy="16" r="3" fill="#4D96FF"></circle></svg>''',
    "pin":        '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"></path><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7"></path><rect x="9" y="2" width="6" height="8" rx="1"></rect></svg>''',
    "blur":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2"><circle cx="12" cy="12" r="9" stroke-dasharray="3 2" opacity="0.5"></circle><circle cx="12" cy="12" r="5" opacity="0.7"></circle><circle cx="12" cy="12" r="2" fill="#FFFFFF"></circle></svg>''',
    "remove_bg":  '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l18 18"></path><path d="M12 3C7 3 3 7 3 12c0 2.5 1 4.8 2.6 6.4"></path><path d="M12 21c5 0 9-4 9-9 0-2.5-1-4.8-2.6-6.4"></path></svg>''',
    "save":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>''',
    "undo":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>''',
    "redo":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path></svg>''',
    "draw":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>''',
    "arrow":      '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="19" x2="19" y2="5"></line><polyline points="9 5 19 5 19 15"></polyline></svg>''',
    "line":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"><line x1="4" y1="20" x2="20" y2="4"></line></svg>''',
    "rect":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="1"></rect></svg>''',
    "circle":     '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2"><ellipse cx="12" cy="12" rx="9" ry="7"></ellipse></svg>''',
    "highlight":  '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2"><rect x="3" y="9" width="18" height="7" rx="2" fill="#FFFF0066"></rect><line x1="7" y1="20" x2="17" y2="20" stroke="#FFD700" stroke-width="1.5"></line></svg>''',
    "number":     '''<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" fill="none" stroke="#FFFFFF" stroke-width="2"></circle><text x="12" y="17" text-anchor="middle" font-size="12" font-weight="bold" fill="#FFFFFF" font-family="sans-serif">1</text></svg>''',
    "callout":    '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>''',
    "copy":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>''',
    "close":      '''<svg viewBox="0 0 24 24" fill="none" stroke="#d9534f" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>''',
    "share":       '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>''',
    "chat":        '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>'''
}

PALETTE_COLORS = [
    "#FF3B3B", "#FF8C00", "#FFD700", "#4CAF50",
    "#00BCD4", "#2196F3", "#9C27B0", "#FF69B4",
    "#FFFFFF", "#AAAAAA", "#555555", "#111111",
]

SHAPE_MODES = {"arrow", "line", "rect", "circle", "highlight", "text", "number", "callout", "draw", "blur"}

def get_svg_icon(key):
    px = QPixmap(24, 24)
    px.fill(Qt.transparent)
    r = QSvgRenderer(SVG_ICONS[key].encode())
    p = QPainter(px)
    r.render(p)
    p.end()
    return QIcon(px)


# ─── Custom styled text input dialog ─────────────────────────────────────────
class TextInputDialog(QDialog):
    def __init__(self, parent=None, title="Add Text", placeholder="Type here…"):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._result = ""

        frame = QFrame(self)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {utils.THEME['surface']};
                border: 2px solid {utils.THEME['primary']};
                border-radius: 14px;
            }}
        """)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(frame)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(18, 14, 18, 14)
        inner.setSpacing(10)

        # Title bar
        hdr = QHBoxLayout()
        title_lbl.setStyleSheet(f"color:{utils.THEME['primary']}; font-weight:bold; font-size:13px;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        close_x = QPushButton("✕")
        close_x.setFixedSize(22, 22)
        close_x.setStyleSheet("""
            QPushButton { background:transparent; color:#888; border:none; font-size:14px; }
            QPushButton:hover { color:#FF5555; }
        """)
        close_x.clicked.connect(self.reject)
        hdr.addWidget(close_x)
        inner.addLayout(hdr)

        # Input field
        self.edit = QTextEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setFixedHeight(80)
        self.edit.setStyleSheet(f"""
            QTextEdit {{
                background: {utils.THEME['background']};
                color: {utils.THEME['text']};
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
            QTextEdit:focus {{ border: 1px solid {utils.THEME['primary']}; }}
        """)
        inner.addWidget(self.edit)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        ok_btn = QPushButton("Add Text")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {utils.THEME['primary']}; color: #1A1A1A; font-weight: bold;
                border: none; border-radius: 8px; padding: 7px 18px; font-size: 12px;
            }}
            QPushButton:hover {{ background: #FF9A70; }}
        """)
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {utils.THEME['background']}; color: {utils.THEME['text_muted']}; font-weight: bold;
                border: 1px solid #444; border-radius: 8px; padding: 7px 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: #444; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        inner.addLayout(btn_row)

        self.setFixedWidth(320)

        # Ctrl+Enter to confirm
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._accept)

    def _accept(self):
        self._result = self.edit.toPlainText().strip()
        if self._result:
            self.accept()

    def get_text(self):
        return self._result

    @staticmethod
    def ask(parent, title="Add Text", placeholder="Type here…"):
        dlg = TextInputDialog(parent, title, placeholder)
        # Center on parent
        if parent:
            pg = parent.mapToGlobal(QPoint(
                (parent.width()  - dlg.width())  // 2,
                (parent.height() - 160) // 2
            ))
            dlg.move(pg)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_text(), True
        return "", False


# ─── Floating tooltip ─────────────────────────────────────────────────────────
class FloatingTooltip(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._lbl = QLabel(self)
        self._lbl.setWordWrap(False)
        self._lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {utils.THEME['background']}; color: {utils.THEME['text']};
                border: 1px solid {utils.THEME['primary']}; border-radius: 5px;
                padding: 5px 10px; font-weight: bold; font-size: 12px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)

    def show_at(self, text, global_pos: QPoint):
        self._lbl.setText(text)
        self._lbl.adjustSize()
        self.adjustSize()
        self.move(global_pos)
        self.show()
        self.raise_()

    def hide_tip(self):
        self.hide()


# ─── Floating palette bar (separate window above popup) ──────────────────────
class PaletteBar(QWidget):
    color_selected = pyqtSignal(str)
    size_changed   = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._frame = QFrame(self)
        self._frame.setStyleSheet(f"""
            QFrame {{
                background-color: {utils.THEME['surface']};
                border: 1px solid #444;
                border-radius: 12px;
            }}
        """)

        # ── Title row at the very top ─────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setContentsMargins(14, 7, 14, 4)
        title_row.setSpacing(0)

        self._title_lbl = QLabel("✦  Annotation Controls")
        self._title_lbl.setStyleSheet(
            "color:#666; font-size:9px; font-weight:bold; letter-spacing:1.2px;"
        )
        title_row.addWidget(self._title_lbl)
        title_row.addStretch()

        self.mode_lbl = QLabel("Draw")
        self.mode_lbl.setStyleSheet(
            "color:#FF7A50; font-weight:bold; font-size:11px;"
        )
        title_row.addWidget(self.mode_lbl)

        # ── Thin divider ──────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background:#444; max-height:1px; margin:0;")

        # ── Controls row ──────────────────────────────────────────────────────
        ctrl_widget = QWidget()
        row = QHBoxLayout(ctrl_widget)
        row.setContentsMargins(12, 6, 12, 8)
        row.setSpacing(10)

        self.size_lbl = QLabel("Size: 2")
        self.size_lbl.setStyleSheet("color:#AAA; font-size:11px; min-width:52px;")
        row.addWidget(self.size_lbl)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 40)
        self.slider.setValue(2)
        self.slider.setFixedWidth(110)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height:4px; background:#444; border-radius:2px; }}
            QSlider::handle:horizontal {{ background:{utils.THEME['primary']}; width:14px; height:14px;
                                         margin:-5px 0; border-radius:7px; }}
        """)
        self.slider.valueChanged.connect(self._on_size)
        row.addWidget(self.slider)

        self.color_sep = QFrame()
        self.color_sep.setFrameShape(QFrame.VLine)
        self.color_sep.setStyleSheet("color:#444; max-height:20px;")
        row.addWidget(self.color_sep)

        self.color_btns = []
        for c in PALETTE_COLORS:
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(f"""
                QPushButton {{ background:{c}; border:2px solid #555; border-radius:10px; }}
                QPushButton:hover {{ border:2px solid #FFF; }}
            """)
            btn.clicked.connect(lambda _, col=c: self.color_selected.emit(col))
            row.addWidget(btn)
            self.color_btns.append(btn)

        self.picker_btn = QPushButton("⊕")
        self.picker_btn.setFixedSize(24, 24)
        self.picker_btn.setStyleSheet("""
            QPushButton {
                background: qconicalgradient(cx:0.5,cy:0.5,angle:0,
                    stop:0 #FF3B3B,stop:0.17 #FFD700,stop:0.33 #4CAF50,
                    stop:0.5 #00BCD4,stop:0.67 #9C27B0,stop:0.83 #FF69B4,stop:1 #FF3B3B);
                border:2px solid #888; border-radius:12px; color:white; font-size:14px;
            }
            QPushButton:hover { border:2px solid #FFF; }
        """)
        self.picker_btn.clicked.connect(self._open_color_picker)
        row.addWidget(self.picker_btn)
        row.addStretch()

        # ── Assemble frame ────────────────────────────────────────────────────
        inner_v = QVBoxLayout(self._frame)
        inner_v.setContentsMargins(0, 0, 0, 0)
        inner_v.setSpacing(0)
        inner_v.addLayout(title_row)
        inner_v.addWidget(div)
        inner_v.addWidget(ctrl_widget)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._frame)

    def _open_color_picker(self):
        color = QColorDialog.getColor(Qt.white, self, "Pick a Color")
        if color.isValid():
            self.color_selected.emit(color.name())

    def _on_size(self, v):
        self.size_lbl.setText(f"Size: {v}")
        self.size_changed.emit(v)

    def set_slider_value(self, v):
        self.slider.blockSignals(True)
        self.slider.setValue(v)
        self.size_lbl.setText(f"Size: {v}")
        self.slider.blockSignals(False)

    def set_mode(self, label, show_colors=True):
        self.mode_lbl.setText(label)
        self.color_sep.setVisible(show_colors)
        self.picker_btn.setVisible(show_colors)
        for btn in self.color_btns:
            btn.setVisible(show_colors)


# ─── Annotation data class ────────────────────────────────────────────────────
class Annotation:
    """One annotation. Blur stores path list, shapes store p1/p2, text stores pos+text."""
    def __init__(self, mode, p1=None, p2=None, color=None, size=2, text=""):
        self.mode   = mode      # "arrow"|"line"|"rect"|"circle"|"highlight"|"text"|"number"
                                # |"callout"|"draw_path"|"blur"
        self.p1     = p1        # QPoint start (or position for text/number)
        self.p2     = p2        # QPoint end
        self.color  = color     # QColor
        self.size   = size      # thickness / font pts
        self.text   = text      # text content for text/callout
        # For freehand pen path
        self.path   = []        # list of QPoint
        # Bounding rect for text (set after placement, for selection border)
        self.bounds = None      # QRect — computed after paint

        # For blur: list of (cx, cy, radius_px) in PIL coords
        self.blur_strokes = []  # [(cx,cy,r), ...]
        self.blur_strength = 8  # GaussianBlur radius


# ─── Interactive image canvas ──────────────────────────────────────────────────
class ImageCanvas(QLabel):
    image_modified = pyqtSignal(object)
    color_picked   = pyqtSignal(str)   # emitted when a colour is eyedropped & copied

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode            = None
        self.drawing         = False
        self.last_point      = QPoint()
        self.hover_point     = None
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"background:{utils.THEME['surface']}; border-radius:8px; border:1px solid #555;")

        self.base_pil_image   = None
        self.current_pixmap   = None   # stable annotated pixmap
        self.draw_color       = QColor("#FF3B3B")
        self.draw_size        = 2      # default 2px
        self.blur_size        = 5      # default 5px

        # Text drag/resize state
        self._dragging_ann    = None   # Annotation being dragged
        self._drag_offset     = QPoint()  # offset from ann.p1 to click point
        self._resizing_ann    = None   # Annotation whose handle is being dragged

        # Resettable timer for size-ring preview (stays alive while slider is dragged)
        self._ring_timer = QTimer()
        self._ring_timer.setSingleShot(True)
        self._ring_timer.setInterval(900)
        self._ring_timer.timeout.connect(self._clear_size_ring)

        self._color_hover_label = None

        # Annotation state
        self._annotations  = []        # list of Annotation
        self._redo_stack   = []
        self._ann_number   = 1

        # In-progress shape drag
        self._shape_start  = None
        self._current_ann  = None

        # In-progress pen path
        self._pen_path     = []

        # In-progress blur stroke
        self._cur_blur_ann = None      # Annotation being built during mouse drag

        # Selected text annotation (for border display)
        self._selected_ann = None

    # ── PIL → canvas size ──────────────────────────────────────────────────
    def set_base_image(self, pil_image):
        self.base_pil_image = pil_image.copy()
        w, h = self.base_pil_image.size
        if w > 900: h = int(h * (900 / w)); w = 900
        if h > 650: w = int(w * (650 / h)); h = 650
        self.setFixedSize(w, h)
        self._redraw_annotations()
        self._update_cursor()

    def _pil_to_pixmap(self, pil_img, w, h):
        byte_io = BytesIO()
        pil_img.save(byte_io, format='PNG')
        px = QPixmap()
        px.loadFromData(byte_io.getvalue())
        return px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _update_cursor(self):
        if self.mode in ("draw", "blur"):
            self.setCursor(Qt.BlankCursor)
        elif self.mode in ("colors", "arrow", "line", "rect", "circle",
                           "highlight", "callout", "number"):
            self.setCursor(Qt.CrossCursor)
        elif self.mode == "text":
            self.setCursor(Qt.IBeamCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # ── Canvas offset helper ───────────────────────────────────────────────
    def _to_canvas(self, qpt):
        if not self.current_pixmap:
            return qpt
        ox = (self.width()  - self.current_pixmap.width())  // 2
        oy = (self.height() - self.current_pixmap.height()) // 2
        return qpt - QPoint(ox, oy)

    def _canvas_size(self):
        if self.current_pixmap:
            return self.current_pixmap.width(), self.current_pixmap.height()
        return self.width(), self.height()

    # ── Scale factors canvas ↔ PIL ─────────────────────────────────────────
    def _scale(self):
        cw, ch = self._canvas_size()
        if not self.base_pil_image or cw == 0 or ch == 0:
            return 1.0, 1.0
        return self.base_pil_image.width / cw, self.base_pil_image.height / ch

    # ─────────────────────────────────────────────────────────────────────────
    # CORE REDRAW: progressive rebuild so blur appears above older annotations
    # and below newer ones, in order.
    # ─────────────────────────────────────────────────────────────────────────
    def _redraw_annotations(self, extra_ann=None):
        """
        Rebuild the annotated pixmap from scratch, processing annotations
        in order so blur correctly covers whatever was drawn before it.
        """
        if not self.base_pil_image:
            return

        cw, ch = self._canvas_size()
        if cw == 0 or ch == 0:
            return

        # We need RGBA to support transparent background
        working_pil = self.base_pil_image.convert("RGBA")

        # We split annotations into "segments":
        # each Blur annotation flattens all preceding shape annotations into PIL,
        # then applies the blur on top.
        shape_queue = []   # shapes accumulated since last blur

        all_anns = self._annotations + ([extra_ann] if extra_ann else [])

        for ann in all_anns:
            if ann.mode == "blur":
                # 1. Bake pending shapes into PIL
                if shape_queue:
                    working_pil = self._bake_shapes_to_pil(working_pil, shape_queue, cw, ch)
                    shape_queue = []
                # 2. Apply blur strokes
                working_pil = self._apply_blur_strokes_to_pil(working_pil, ann)
            else:
                shape_queue.append(ann)

        # Convert working PIL to canvas pixmap
        self.current_pixmap = self._pil_to_pixmap(working_pil, cw, ch)

        # 3. Paint remaining shape annotations on QPainter
        if shape_queue:
            painter = QPainter(self.current_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            for ann in shape_queue:
                self._paint_annotation(painter, ann)
            painter.end()

        # Draw selection border for selected text
        if self._selected_ann and self._selected_ann.bounds:
            painter = QPainter(self.current_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor("#FF7A50"), 1.5, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self._selected_ann.bounds.adjusted(-4, -4, 4, 4))
            # Resize handle (bottom-right corner)
            hr = self._selected_ann.bounds.adjusted(-4, -4, 4, 4)
            painter.setBrush(QBrush(QColor("#FF7A50")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(hr.right(), hr.bottom()), 5, 5)
            painter.end()

        self.setPixmap(self.current_pixmap)

    def _bake_shapes_to_pil(self, pil_img, shape_queue, cw, ch):
        """Draw shape_queue onto a QPixmap copy of pil_img, then convert back to PIL."""
        px = self._pil_to_pixmap(pil_img, cw, ch)
        painter = QPainter(px)
        painter.setRenderHint(QPainter.Antialiasing)
        for ann in shape_queue:
            self._paint_annotation(painter, ann)
        painter.end()
        # Convert QPixmap → PIL
        qimg = px.toImage().convertToFormat(QImage.Format_RGBA8888)
        w2, h2 = qimg.width(), qimg.height()
        ptr = qimg.bits(); ptr.setsize(w2 * h2 * 4)
        baked = Image.frombuffer('RGBA', (w2, h2), bytes(ptr), 'raw', 'RGBA', 0, 1)
        # Scale back to PIL resolution
        baked = baked.resize(pil_img.size, resample=Image.Resampling.LANCZOS)
        return baked

    def _apply_blur_strokes_to_pil(self, pil_img, ann):
        """Apply all blur strokes of ann to pil_img, return new PIL image."""
        from PIL import ImageFilter, ImageDraw
        result = pil_img.convert("RGBA")
        for (cx, cy, r) in ann.blur_strokes:
            x1 = max(0, cx - r); y1 = max(0, cy - r)
            x2 = min(pil_img.width,  cx + r); y2 = min(pil_img.height, cy + r)
            if x2 <= x1 or y2 <= y1:
                continue
            crop    = result.crop((x1, y1, x2, y2))
            blurred = crop.filter(ImageFilter.GaussianBlur(radius=ann.blur_strength))
            mask    = Image.new("L", crop.size, 0)
            ImageDraw.Draw(mask).ellipse([0, 0, crop.size[0]-1, crop.size[1]-1], fill=255)
            result.paste(blurred, (x1, y1), mask=mask)
        return result

    # ── Paint one annotation via QPainter ─────────────────────────────────
    def _paint_annotation(self, painter, ann):
        c  = ann.color or self.draw_color
        sz = max(1, ann.size)

        if ann.mode == "draw_path":
            pen = QPen(c, sz, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            if len(ann.path) >= 2:
                for i in range(len(ann.path) - 1):
                    painter.drawLine(ann.path[i], ann.path[i+1])
            elif ann.path:
                painter.drawPoint(ann.path[0])

        elif ann.mode == "line":
            painter.setPen(QPen(c, sz, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(ann.p1, ann.p2)

        elif ann.mode == "arrow":
            painter.setPen(QPen(c, sz, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(c))
            self._draw_arrow(painter, ann.p1, ann.p2, sz)

        elif ann.mode == "rect":
            painter.setPen(QPen(c, sz, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRect(ann.p1, ann.p2).normalized())

        elif ann.mode == "circle":
            painter.setPen(QPen(c, sz, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRect(ann.p1, ann.p2).normalized())

        elif ann.mode == "highlight":
            hc = QColor(c); hc.setAlpha(90)
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(hc))
            r = QRect(ann.p1, ann.p2).normalized()
            r.setHeight(max(r.height(), max(sz * 3, 12)))
            painter.drawRect(r)

        elif ann.mode == "text":
            font = QFont("Segoe UI", max(8, sz * 2))
            font.setBold(True)
            painter.setFont(font)
            # Drop shadow
            painter.setPen(QPen(QColor(0, 0, 0, 140)))
            painter.drawText(ann.p1 + QPoint(1, 1), ann.text or "Text")
            painter.setPen(QPen(c))
            painter.drawText(ann.p1, ann.text or "Text")
            # Measure bounding rect for selection handle
            fm = QFontMetrics(font)
            txt = ann.text or "Text"
            ann.bounds = QRect(ann.p1.x(), ann.p1.y() - fm.ascent(),
                               fm.horizontalAdvance(txt), fm.height())

        elif ann.mode == "number":
            r = max(10, sz * 2)
            center = ann.p1
            painter.setPen(QPen(c, 2))
            painter.setBrush(QBrush(c))
            painter.drawEllipse(center, r, r)
            luma = c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114
            text_col = QColor("#000000") if luma > 128 else QColor("#FFFFFF")
            painter.setPen(QPen(text_col))
            font = QFont("Segoe UI", max(7, r - 3))
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRect(center.x()-r, center.y()-r, r*2, r*2),
                             Qt.AlignCenter, str(ann.text))

        elif ann.mode == "callout":
            rect = QRect(ann.p1, ann.p2).normalized()
            if rect.width() < 20 or rect.height() < 16:
                return
            bg = QColor(c); bg.setAlpha(220)
            painter.setPen(QPen(c, max(1, sz)))
            painter.setBrush(QBrush(bg))
            painter.drawRoundedRect(rect, 8, 8)
            if rect.height() > 12:
                tx = rect.left() + rect.width() // 4
                ty = rect.bottom()
                tail = QPolygon([QPoint(tx-8,ty), QPoint(tx+8,ty), QPoint(tx, ty+14)])
                painter.setPen(Qt.NoPen); painter.setBrush(QBrush(bg))
                painter.drawPolygon(tail)
            if ann.text:
                luma = c.red()*0.299 + c.green()*0.587 + c.blue()*0.114
                tc = QColor("#000000") if luma > 128 else QColor("#FFFFFF")
                painter.setPen(QPen(tc))
                font = QFont("Segoe UI", max(9, sz + 3))
                painter.setFont(font)
                painter.drawText(rect.adjusted(6,4,-6,-4), Qt.AlignCenter|Qt.TextWordWrap, ann.text)

    def _draw_arrow(self, painter, p1, p2, thickness):
        painter.drawLine(p1, p2)
        dx = p2.x() - p1.x(); dy = p2.y() - p1.y()
        length = max(1, math.hypot(dx, dy))
        ux, uy = dx/length, dy/length
        hlen = max(10, thickness * 4); hw = max(5, thickness * 2)
        bx = p2.x() - ux*hlen; by = p2.y() - uy*hlen
        px2 = -uy*hw; py2 = ux*hw
        arrow = QPolygon([p2, QPoint(int(bx+px2), int(by+py2)), QPoint(int(bx-px2), int(by-py2))])
        painter.drawPolygon(arrow)

    # ── Mouse Press ────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        pt = self._to_canvas(e.pos())

        if self.mode == "colors":
            self._pick_color_at(pt, copy=True)

        elif self.mode == "draw":
            self.drawing = True
            self._pen_path = [pt]
            self._draw_point_on_pixmap(pt, first=True)

        elif self.mode == "blur":
            self.drawing = True
            sx, sy = self._scale()
            r = max(3, int(self.blur_size * (sx+sy)/2))
            cx = int(pt.x() * sx); cy = int(pt.y() * sy)
            self._cur_blur_ann = Annotation("blur", color=self.draw_color, size=self.blur_size)
            self._cur_blur_ann.blur_strength = max(2, self.blur_size // 3)
            self._cur_blur_ann.blur_strokes.append((cx, cy, r))
            self._redraw_annotations(extra_ann=self._cur_blur_ann)
            self._paint_blur_cursor(pt)

        elif self.mode == "text":
            clicked = self._ann_at(pt)
            if clicked:
                # Check if clicking the resize handle (bottom-right corner of bounds)
                if clicked.bounds:
                    hr = clicked.bounds.adjusted(-4, -4, 4, 4)
                    handle_pt = QPoint(hr.right(), hr.bottom())
                    if (pt - handle_pt).manhattanLength() <= 10:
                        self._resizing_ann = clicked
                        self._selected_ann = clicked
                        return
                # Click on body → start drag
                self._selected_ann = clicked
                self._dragging_ann = clicked
                self._drag_offset  = pt - clicked.p1
                self._redraw_annotations()
            else:
                self._selected_ann = None
                self._dragging_ann = None
                self._resizing_ann = None
                self._ask_text_and_place(pt, "text")

        elif self.mode == "number":
            ann = Annotation("number", p1=pt, p2=pt,
                             color=self.draw_color, size=self.draw_size,
                             text=str(self._ann_number))
            self._commit_annotation(ann)
            self._ann_number += 1

        elif self.mode == "callout":
            self._shape_start = pt
            self._current_ann = Annotation("callout", p1=pt, p2=pt,
                                           color=self.draw_color, size=self.draw_size)
        elif self.mode in SHAPE_MODES:
            self._shape_start = pt
            self._current_ann = Annotation(self.mode, p1=pt, p2=pt,
                                           color=self.draw_color, size=self.draw_size)

    # ── Mouse Move ─────────────────────────────────────────────────────────
    def mouseMoveEvent(self, e):
        pt = self._to_canvas(e.pos())
        self.hover_point = pt

        if self.mode == "colors":
            self._pick_color_at(pt, copy=False)

        elif self.mode == "text" and self._resizing_ann:
            # Drag handle → change font size based on horizontal distance
            ann = self._resizing_ann
            dx = max(0, pt.x() - ann.p1.x())
            ann.size = max(1, dx // 6)
            self._redraw_annotations()

        elif self.mode == "text" and self._dragging_ann:
            # Drag body → move annotation
            self._dragging_ann.p1 = pt - self._drag_offset
            self._dragging_ann.p2 = self._dragging_ann.p1
            self._redraw_annotations()

        elif self.mode == "text":
            # Hover: update cursor based on proximity to existing text handles
            hit = self._ann_at(pt)
            if hit and hit.bounds:
                hr = hit.bounds.adjusted(-4, -4, 4, 4)
                handle_pt = QPoint(hr.right(), hr.bottom())
                if (pt - handle_pt).manhattanLength() <= 12:
                    self.setCursor(Qt.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.SizeAllCursor)   # over text body → move cursor
            else:
                self.setCursor(Qt.IBeamCursor)

        elif self.mode == "draw" and self.drawing:
            if self._pen_path:
                self._pen_path.append(pt)
                self._draw_line_on_pixmap(self._pen_path[-2], pt)

        elif self.mode == "draw":
            self._paint_pen_cursor(pt)

        elif self.mode == "blur" and self.drawing and self._cur_blur_ann:
            sx, sy = self._scale()
            r = max(3, int(self.blur_size * (sx+sy)/2))
            cx = int(pt.x() * sx); cy = int(pt.y() * sy)
            self._cur_blur_ann.blur_strokes.append((cx, cy, r))
            # Just draw fake transparent brush preview during drag to avoid lag
            self._draw_blur_stroke_on_pixmap(pt)

        elif self.mode == "blur":
            self._paint_blur_cursor(pt)

        elif self.mode in SHAPE_MODES and self._current_ann and self._shape_start:
            self._current_ann.p2 = pt
            self._redraw_annotations(extra_ann=self._current_ann)

    # ── Mouse Release ──────────────────────────────────────────────────────
    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        pt = self._to_canvas(e.pos())

        if self.mode == "text" and (self._dragging_ann or self._resizing_ann):
            self._dragging_ann  = None
            self._resizing_ann  = None
            self._redraw_annotations()
            return

        if self.mode == "draw" and self.drawing:
            self.drawing = False
            ann = Annotation("draw_path", p1=self._pen_path[0] if self._pen_path else pt,
                             p2=pt, color=self.draw_color, size=self.draw_size)
            ann.path = list(self._pen_path)
            self._pen_path = []
            self._commit_annotation(ann)

        elif self.mode == "blur" and self.drawing and self._cur_blur_ann:
            self.drawing = False
            # Commit the blur annotation
            self._commit_annotation(self._cur_blur_ann)
            self._cur_blur_ann = None

        elif self.mode == "callout" and self._current_ann:
            self._current_ann.p2 = pt
            rect = QRect(self._current_ann.p1, pt).normalized()
            if rect.width() >= 20 and rect.height() >= 16:
                text, ok = TextInputDialog.ask(self.parent(), "Callout Text", "Enter callout text…")
                if ok:
                    self._current_ann.text = text
                    self._commit_annotation(self._current_ann)
            self._current_ann = None
            self._shape_start = None
            self._redraw_annotations()

        elif self.mode in SHAPE_MODES and self._current_ann and self._shape_start:
            self._current_ann.p2 = pt
            if self._current_ann.mode not in ("number",):
                self._commit_annotation(self._current_ann)
            self._current_ann = None
            self._shape_start = None

    # ── Leave ──────────────────────────────────────────────────────────────
    def leaveEvent(self, e):
        self.hover_point = None
        if self.current_pixmap:
            self.setPixmap(self.current_pixmap)
        if self.mode == "colors" and self._color_hover_label:
            self._color_hover_label.hide()

    # ── Freehand pen painting (live on pixmap) ─────────────────────────────
    def _draw_point_on_pixmap(self, pt, first=False):
        if not self.current_pixmap:
            return
        painter = QPainter(self.current_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.draw_color, max(1, self.draw_size),
                   Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPoint(pt)
        painter.end()
        self._paint_pen_cursor(pt)

    def _draw_line_on_pixmap(self, p1, p2):
        if not self.current_pixmap or len(self._pen_path) < 2:
            return
        painter = QPainter(self.current_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.draw_color, max(1, self.draw_size),
                   Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()
        self._paint_pen_cursor(p2)

    def _draw_blur_stroke_on_pixmap(self, pt):
        if not self.current_pixmap:
            return
        painter = QPainter(self.current_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.blur_size
        painter.setPen(Qt.NoPen)
        # Fake blur visually as a translucent gray stroke
        painter.setBrush(QBrush(QColor(100, 100, 100, 60)))
        painter.drawEllipse(pt, r, r)
        painter.end()
        self._paint_blur_cursor(pt)

    # ── Cursor previews ────────────────────────────────────────────────────
    def _paint_pen_cursor(self, pt):
        if not self.current_pixmap:
            return
        preview = self.current_pixmap.copy()
        p = QPainter(preview)
        p.setRenderHint(QPainter.Antialiasing)
        r = max(1, self.draw_size // 2)
        p.setPen(QPen(QColor(255,255,255,200), 1.5))
        p.setBrush(QBrush(QColor(self.draw_color.red(), self.draw_color.green(),
                                  self.draw_color.blue(), 160)))
        p.drawEllipse(pt, r, r)
        p.end()
        self.setPixmap(preview)

    def _paint_blur_cursor(self, pt):
        if not self.current_pixmap:
            return
        preview = self.current_pixmap.copy()
        p = QPainter(preview)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.blur_size
        p.setPen(QPen(QColor(255,255,255,220), 1.5, Qt.DashLine))
        p.setBrush(QBrush(QColor(180,200,255,35)))
        p.drawEllipse(pt, r, r)
        p.end()
        self.setPixmap(preview)

    # ── Size indicator (shown on slider change) ────────────────────────────
    def show_size_ring(self):
        """Flash a size preview in centre of canvas for 700 ms."""
        if not self.current_pixmap:
            return
        cw, ch = self._canvas_size()
        cx, cy = cw // 2, ch // 2
        preview = self.current_pixmap.copy()
        p = QPainter(preview)
        p.setRenderHint(QPainter.Antialiasing)

        if self.mode == "blur":
            r = max(4, self.blur_size)
            p.setPen(QPen(QColor(180, 200, 255, 220), 1.5, Qt.DashLine))
            p.setBrush(QBrush(QColor(180, 200, 255, 40)))
            p.drawEllipse(QPoint(cx, cy), r, r)
        elif self.mode in ("text", "callout", "number"):
            # Show sample text at the current font size
            fs = max(6, self.draw_size * 2)
            font = QFont("Segoe UI", fs, QFont.Bold)
            p.setFont(font)
            p.setPen(QPen(self.draw_color))
            fm = QFontMetrics(font)
            sample = "Abc"
            tw = fm.horizontalAdvance(sample)
            p.drawText(QPoint(cx - tw // 2, cy + fm.ascent() // 2), sample)
        else:
            r = max(1, self.draw_size // 2)
            p.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
            p.setBrush(QBrush(QColor(self.draw_color.red(),
                                     self.draw_color.green(),
                                     self.draw_color.blue(), 200)))
            p.drawEllipse(QPoint(cx, cy), r, r)

        p.end()
        self.setPixmap(preview)
        # Restart the resettable timer — ring stays alive during continuous dragging
        self._ring_timer.start()

    def _clear_size_ring(self):
        if self.current_pixmap:
            self.setPixmap(self.current_pixmap)

    # ── Color picker ───────────────────────────────────────────────────────
    def _pick_color_at(self, canvas_pt, copy=False):
        if not self.base_pil_image or not self.current_pixmap:
            return None
        sx, sy = self._scale()
        px = int(max(0, min(canvas_pt.x() * sx, self.base_pil_image.width  - 1)))
        py = int(max(0, min(canvas_pt.y() * sy, self.base_pil_image.height - 1)))
        pixel = self.base_pil_image.convert('RGB').getpixel((px, py))
        r2, g, b = pixel[:3]
        hex_color = f"#{r2:02X}{g:02X}{b:02X}"
        luma = r2 * 0.299 + g * 0.587 + b * 0.114

        lbl = self._color_hover_label
        if lbl:
            lbl.setText(hex_color)
            tc = "#000000" if luma > 128 else "#FFFFFF"
            lbl.setStyleSheet(f"""
                QLabel {{ background-color:{hex_color}; color:{tc};
                          border:2px solid white; border-radius:6px;
                          padding:3px 8px; font-weight:bold; font-size:12px; }}
            """)
            lbl.adjustSize()
            lx = canvas_pt.x() + 16
            ly = canvas_pt.y() - lbl.height() // 2
            lx = min(lx, self.width()  - lbl.width()  - 4)
            ly = max(4,  min(ly, self.height() - lbl.height() - 4))
            lbl.move(lx, ly); lbl.raise_(); lbl.show()

        if copy:
            try:
                import pyperclip
                pyperclip.copy(hex_color)
            except Exception:
                pass
            self.color_picked.emit(hex_color)   # → popup shows toast
            return hex_color
        return None

    # ── Annotation find hit-test ───────────────────────────────────────────
    def _ann_at(self, pt):
        """Find topmost annotation whose bounding box contains pt."""
        for ann in reversed(self._annotations):
            if ann.mode == "text" and ann.bounds:
                if ann.bounds.adjusted(-6, -6, 6, 6).contains(pt):
                    return ann
        return None

    # ── Commit / undo / redo ───────────────────────────────────────────────
    def _commit_annotation(self, ann):
        self._annotations.append(ann)
        self._redo_stack.clear()
        self._redraw_annotations()
        self.image_modified.emit(self.base_pil_image)

    def undo_annotation(self):
        if self._annotations:
            popped = self._annotations.pop()
            self._redo_stack.append(popped)
            self._ann_number = sum(1 for a in self._annotations if a.mode == "number") + 1
            self._redraw_annotations()
            return True
        return False

    def redo_annotation(self):
        if self._redo_stack:
            ann = self._redo_stack.pop()
            self._annotations.append(ann)
            self._ann_number = sum(1 for a in self._annotations if a.mode == "number") + 1
            self._redraw_annotations()
            return True
        return False

    def clear_annotations(self):
        self._annotations.clear(); self._redo_stack.clear()
        self._ann_number = 1; self._redraw_annotations()

    # ── Text placement ─────────────────────────────────────────────────────
    def _ask_text_and_place(self, pt, mode):
        text, ok = TextInputDialog.ask(self.parent(), "Add Text", "Enter text to place…")
        if ok and text:
            ann = Annotation(mode, p1=pt, p2=pt,
                             color=self.draw_color, size=self.draw_size, text=text)
            self._commit_annotation(ann)
            self._selected_ann = ann
            self._redraw_annotations()

    # ── Size / color from palette ──────────────────────────────────────────
    def set_draw_size(self, v):
        self.draw_size = v
        self.show_size_ring()

    def set_blur_size(self, v):
        self.blur_size = v
        self._update_cursor()
        self.show_size_ring()

    def set_draw_color(self, hex_color):
        self.draw_color = QColor(hex_color)

    # ── Flatten annotations into base PIL (for save/copy/pin) ──────────────
    def get_flattened_pil(self):
        """Return base PIL image with all annotations baked in."""
        if not self.base_pil_image:
            return None
        cw, ch = self._canvas_size()
        working_pil = self.base_pil_image.copy()
        shape_queue = []
        for ann in self._annotations:
            if ann.mode == "blur":
                if shape_queue:
                    working_pil = self._bake_shapes_to_pil(working_pil, shape_queue, cw, ch)
                    shape_queue = []
                working_pil = self._apply_blur_strokes_to_pil(working_pil, ann)
            else:
                shape_queue.append(ann)
        if shape_queue:
            working_pil = self._bake_shapes_to_pil(working_pil, shape_queue, cw, ch)
        return working_pil


# ─── Main popup ───────────────────────────────────────────────────────────────
class CaptureSuitePopup(QWidget):
    ask_ai = pyqtSignal(object) # image context
    
    def __init__(self, context_data, parent_app=None):
        super().__init__()
        self.context_data  = context_data
        self.parent_app    = parent_app
        self.image         = context_data.get("image")
        self.image_history = []
        self.image_redo    = []
        self.executor      = ActionExecutor()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._tooltip         = FloatingTooltip()
        self._active_tool_btn = None
        # PaletteBar created inside init_ui as a floating window above popup
        self._palette         = None

        self.init_ui()

    # ─── Build UI ────────────────────────────────────────────────────────────
    def init_ui(self):
        self.central_frame = QFrame(self)
        self.central_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {utils.THEME['background']};
                border-radius: 12px; border: 1px solid #444;
            }}
        """)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.addWidget(self.central_frame)

        # ── Vertical root inside the frame: [canvas + toolbar] ─────────────
        root_v = QVBoxLayout(self.central_frame)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.setSpacing(0)

        # ── Floating palette bar (lives outside the frame, above popup) ───────
        self._palette = PaletteBar(self)   # top-level floating window
        self._palette.color_selected.connect(self._on_color)
        self._palette.size_changed.connect(self._on_size)
        # hidden until a tool is activated; shown by _show_palette()

        # ── Content row: canvas | sep | toolbar ──────────────────────────────
        inner = QHBoxLayout()
        inner.setContentsMargins(18, 18, 18, 18)
        inner.setSpacing(16)
        root_v.addLayout(inner)

        # Canvas
        self.canvas = ImageCanvas(self)
        self.canvas.set_base_image(self.image)
        self.canvas.color_picked.connect(lambda hx: self.show_toast(f"Copied {hx} ✓", duration=1400))
        self.canvas.image_modified.connect(self._on_canvas_modified)
        inner.addWidget(self.canvas)

        self._color_lbl = QLabel(self.canvas)
        self._color_lbl.hide()
        self.canvas._color_hover_label = self._color_lbl

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#444;")
        inner.addWidget(sep)

        # ── Toolbar ───────────────────────────────────────────────────────
        tb = QVBoxLayout()
        tb.setAlignment(Qt.AlignTop)
        tb.setSpacing(5)

        def section(label):
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#555; font-size:9px; font-weight:bold; padding:3px 0 1px 0;")
            lbl.setAlignment(Qt.AlignCenter)
            tb.addWidget(lbl)

        def mkbtn(key, label, fn, bg=None, hov=None, is_text_btn=False):
            btn = QPushButton()
            if is_text_btn:
                btn.setText(key)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background:{bg or utils.THEME['surface']}; color:#FFFFFF;
                        border:1px solid #555; border-radius:8px;
                        font-size:16px; font-weight:bold;
                    }}
                    QPushButton:hover {{
                        background:{hov or '#444'};
                        border:1px solid {utils.THEME['primary']};
                    }}
                """)
            else:
                btn.setIcon(get_svg_icon(key))
                btn.setIconSize(QSize(18, 18))
                self._style(btn, bg=bg, hover=hov)
            btn.setFixedSize(36, 36)
            btn.tool_label = label
            btn.installEventFilter(self)
            btn._toggleable = True
            btn.clicked.connect(fn)
            return btn

        def add_row(*btns):
            row = QHBoxLayout()
            row.setSpacing(4)
            for b in btns: row.addWidget(b)
            tb.addLayout(row)

        # ACTIONS
        section("ACTIONS")
        save_btn  = mkbtn("save",  "Save Image",        lambda: self.run_save(),  "#28A745","#218838")
        copy_btn  = mkbtn("copy",  "Copy to Clipboard", lambda: self.run_copy(),  "#1565C0","#1976D2")
        add_row(save_btn, copy_btn)

        undo_btn  = mkbtn("undo",  "Undo (Ctrl+Z)", lambda: self.run_undo(),  "#6B3300","#7B4000")
        redo_btn  = mkbtn("redo",  "Redo (Ctrl+Y)", lambda: self.run_redo(),  "#3A2800","#4A3500")
        add_row(undo_btn, redo_btn)

        share_btn = mkbtn("share", "Share Link (Upload)", lambda: self.run_share(), "#6A0DAD","#8B30D4")
        add_row(share_btn)

        # DRAW
        section("DRAW")
        pen_btn = mkbtn("draw",      "Pen",         lambda: self._toggle("draw",      pen_btn,  "Pen",       True))
        hi_btn  = mkbtn("highlight", "Highlighter", lambda: self._toggle("highlight", hi_btn,   "Highlight", True))
        add_row(pen_btn, hi_btn)

        # SHAPES
        section("SHAPES")
        arr_btn  = mkbtn("arrow",  "Arrow",     lambda: self._toggle("arrow",  arr_btn,  "Arrow",    True))
        line_btn = mkbtn("line",   "Line",      lambda: self._toggle("line",   line_btn, "Line",     True))
        add_row(arr_btn, line_btn)

        rect_btn = mkbtn("rect",   "Rectangle", lambda: self._toggle("rect",   rect_btn, "Rect",     True))
        circ_btn = mkbtn("circle", "Circle",    lambda: self._toggle("circle", circ_btn, "Circle",   True))
        add_row(rect_btn, circ_btn)

        # ANNOTATE
        section("ANNOTATE")
        # Text button — use letter T with proper font, not SVG
        txt_btn  = mkbtn("T", "Text Label", lambda: self._toggle("text", txt_btn, "Text", True),
                          is_text_btn=True)
        num_btn  = mkbtn("number",  "Numbered Label",  lambda: self._toggle("number",  num_btn,  "Number",  True))
        add_row(txt_btn, num_btn)

        call_btn = mkbtn("callout", "Callout Bubble",  lambda: self._toggle("callout", call_btn, "Callout", True))
        blur_btn = mkbtn("blur",    "Blur Brush",      lambda: self._toggle("blur",    blur_btn, "Blur",    False))
        add_row(call_btn, blur_btn)

        # ANALYZE
        section("ANALYZE")
        ocr_btn  = mkbtn("ocr",    "Extract Text (OCR)", lambda: self.run_ocr())
        chat_btn = mkbtn("chat",   "Ask AI about Snip",  lambda: self.run_ask_ai())
        add_row(ocr_btn, chat_btn)
        
        qr_btn   = mkbtn("qr",      "Scan QR / Barcode",  lambda: self.run_qr())
        col_btn  = mkbtn("colors",  "Color Picker",       lambda: self._toggle("colors", col_btn, "Eyedropper", False))
        add_row(qr_btn, col_btn)

        # PIN and CLOSE side by side
        section("WINDOW")
        pin_btn = mkbtn("pin", "Pin to Screen", lambda: self.run_pin())

        cls_btn = QPushButton()
        cls_btn.setIcon(get_svg_icon("close"))
        cls_btn.setIconSize(QSize(20, 20))
        cls_btn.setFixedSize(36, 36)
        cls_btn.tool_label = "Close (Esc)"
        cls_btn.installEventFilter(self)
        cls_btn._toggleable = False
        self._style(cls_btn, bg="transparent", hover="#c9302c", text="#d9534f")
        cls_btn.clicked.connect(self.close)
        add_row(pin_btn, cls_btn)

        inner.addLayout(tb)

        self.oldPos = self.pos()
        self.central_frame.installEventFilter(self)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.run_undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.run_redo)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.run_copy)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._on_escape)

    # ─── Style helpers ────────────────────────────────────────────────────────
    def _style(self, btn, bg=None, hover=None, text=None, active=False):
        bg    = bg    or utils.THEME['surface']
        hover = hover or "#444"
        text  = text  or utils.THEME['text']
        border = f"2px solid {utils.THEME['primary']}" if active else "1px solid #555"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{bg}; color:{text};
                border:{border}; border-radius:8px;
            }}
            QPushButton:hover {{
                background-color:{hover};
                border:1px solid {utils.THEME['primary']};
            }}
        """)

    # ─── Mode toggle ──────────────────────────────────────────────────────────
    def _toggle(self, mode, btn, palette_label, show_colors):
        if self.canvas.mode == mode:
            self._deactivate()
        else:
            self._deactivate()
            self.canvas.mode = mode
            self.canvas._update_cursor()
            self._active_tool_btn = btn
            self._style(btn, bg="#252525", active=True)
            # Always reset slider to 1 when switching to a new tool
            if mode == "blur":
                self.canvas.blur_size = 5
                self._palette.set_slider_value(5)
            else:
                self.canvas.draw_size = 2
                self._palette.set_slider_value(2)
            self._show_palette(palette_label, show_colors)

    def _deactivate(self):
        if self.canvas.mode:
            self.canvas.mode = None
            self.canvas._update_cursor()
            self._hide_palette()
            if self._color_lbl:
                self._color_lbl.hide()
        if self._active_tool_btn:
            self._style(self._active_tool_btn)
            self._active_tool_btn = None

    def _on_escape(self):
        if self.canvas.mode:
            self._deactivate()
        else:
            self.close()

    # ─── Palette signals ──────────────────────────────────────────────────────
    def _on_color(self, c):
        self.canvas.set_draw_color(c)

    def _on_size(self, v):
        if self.canvas.mode == "blur":
            self.canvas.set_blur_size(v)
        else:
            self.canvas.set_draw_size(v)

    # ─── Palette: show/hide the floating bar above popup ─────────────────────
    def _show_palette(self, label, show_colors=True):
        if not show_colors:
            self._hide_palette()
            return
        self._palette.set_mode(label, show_colors=show_colors)
        self._palette.adjustSize()
        self._reposition_palette()
        self._palette.show()
        self._palette.raise_()

    def _hide_palette(self):
        self._palette.hide()

    def _reposition_palette(self):
        """Keep the floating palette centred just above the main popup."""
        if not self._palette:
            return
        gpos = self.mapToGlobal(QPoint(0, 0))
        pal_w = max(self._palette.sizeHint().width(), self._palette.width(), 200)
        pal_h = max(self._palette.sizeHint().height(), self._palette.height(), 60)
        px = gpos.x() + (self.width() - pal_w) // 2
        py = gpos.y() - pal_h - 6
        screen = QApplication.desktop().screenGeometry()
        px = max(screen.left() + 4, min(px, screen.right() - pal_w - 4))
        py = max(screen.top() + 4, py)
        self._palette.move(px, py)

    # ─── Toast ────────────────────────────────────────────────────────────────
    def show_toast(self, msg, duration=1800):
        self._tooltip.hide_tip()
        self._tooltip._lbl.setText(msg)
        self._tooltip._lbl.adjustSize()
        self._tooltip.adjustSize()
        gpos = self.mapToGlobal(QPoint(0, 0))
        tx = gpos.x() + (self.width()  - self._tooltip.width())  // 2
        ty = gpos.y() + self.height() - self._tooltip.height() - 14
        self._tooltip.move(tx, ty)
        self._tooltip.show(); self._tooltip.raise_()
        QTimer.singleShot(duration, self._tooltip.hide_tip)

    # ─── Canvas signal ────────────────────────────────────────────────────────
    def _on_canvas_modified(self, img):
        self.image_history.append(self.image.copy())
        self.image_redo.clear()
        # Don't reassign self.image here; annotations are non-destructive

    # ─── Actions ──────────────────────────────────────────────────────────────
    def _get_flat(self):
        """Get PIL image with all annotations baked in."""
        flat = self.canvas.get_flattened_pil()
        return flat if flat else self.image

    def run_save(self):
        flat = self._get_flat()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Snip", "Coral_Snip.png",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;All (*.*)"
        )
        if path:
            flat.save(path)
            self.show_toast("Saved ✓")

    def run_copy(self):
        flat = self._get_flat()
        byte_io = BytesIO()
        flat.save(byte_io, format='PNG')
        qimg = QImage()
        qimg.loadFromData(byte_io.getvalue())
        QApplication.clipboard().setImage(qimg)
        self.show_toast("Copied to clipboard")

    def run_share(self):
        """Upload the annotated snip to 0x0.st in a background thread and show the link."""
        flat = self._get_flat()
        self.show_toast("Uploading...", duration=15000)
        import threading
        from io import BytesIO as _BytesIO

        def _upload():
            try:
                import requests
                buf = _BytesIO()
                flat.save(buf, format="PNG")
                buf.seek(0)
                r = requests.post(
                    "https://tmpfiles.org/api/v1/upload",
                    files={"file": ("coral_snip.png", buf, "image/png")},
                    timeout=20
                )
                if r.status_code == 200:
                    import json
                    url = json.loads(r.text)["data"]["url"].replace("http://", "https://")
                    # Copy URL to clipboard and show result — done via signal on main thread
                    # Show result in main thread
                    from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(
                        self, "_on_share_done",
                        Qt.QueuedConnection,
                        Q_ARG(str, url),
                        Q_ARG(bool, True)
                    )
                else:
                    QMetaObject.invokeMethod(
                        self, "_on_share_done",
                        Qt.QueuedConnection,
                        Q_ARG(str, f"Upload failed ({r.status_code})"),
                        Q_ARG(bool, False)
                    )
            except Exception as e:
                from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    self, "_on_share_done",
                    Qt.QueuedConnection,
                    Q_ARG(str, str(e)),
                    Q_ARG(bool, False)
                )

        threading.Thread(target=_upload, daemon=True).start()

    @pyqtSlot(str, bool)
    def _on_share_done(self, result, success):
        if success:
            # Copy URL to clipboard on main thread (safe)
            QApplication.clipboard().setText(result)
            self.show_toast("Link copied to clipboard! \U0001F517", duration=4000)
        else:
            self.show_toast(f"Upload failed: {result}", duration=4000)

    def run_undo(self):
        if self.canvas.undo_annotation():
            pass
        elif self.image_history:
            self.image_redo.append(self.image.copy())
            self.image = self.image_history.pop()
            self.canvas.base_pil_image = self.image.copy()
            self.canvas._annotations.clear()
            self.canvas._redraw_annotations()
        else:
            pass

    def run_redo(self):
        if self.canvas.redo_annotation():
            pass
        elif self.image_redo:
            self.image_history.append(self.image.copy())
            self.image = self.image_redo.pop()
            self.canvas.base_pil_image = self.image.copy()
            self.canvas._annotations.clear()
            self.canvas._redraw_annotations()
        else:
            pass

    def run_ocr(self):
        """Run OCR directly on current flattened image."""
        self.show_toast("Running OCR…", duration=10000)
        QApplication.processEvents()
        import threading, os

        flat = self._get_flat()

        def _do_ocr():
            try:
                import pytesseract
                # Auto-detect Tesseract on Windows
                for tess_path in [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                ]:
                    if os.path.exists(tess_path):
                        pytesseract.pytesseract.tesseract_cmd = tess_path
                        break

                # Ensure image is RGB (tesseract dislikes RGBA/P modes)
                img_rgb = flat.convert("RGB")

                # Try multiple PSM modes for best detection
                best_text = ""
                # --- Image Preprocessing for much higher accuracy ---
                img_proc = flat.convert("L") # grayscale
                from PIL import Image, ImageEnhance
                w, h = img_proc.size
                img_proc = img_proc.resize((w*2, h*2), Image.Resampling.LANCZOS)
                enhancer = ImageEnhance.Contrast(img_proc)
                img_proc = enhancer.enhance(2.0)

                # Try multiple PSM modes for best detection
                best_text = ""
                for psm in (6, 3): 
                    cfg = f"--oem 3 --psm {psm}"
                    t = pytesseract.image_to_string(img_proc, lang="eng", config=cfg).strip()
                    if len(t) > len(best_text):
                        best_text = t

                if best_text:
                    chars = len(best_text)
                    utils.setup_logger(__name__).info(f"OCR Success: {chars} characters extracted.")
                    QTimer.singleShot(0, lambda: self.show_toast(
                        f"OCR Success! {chars} characters found.", duration=2500))
                    # Show full result in a high-priority popup
                    QTimer.singleShot(50, lambda: self._show_ocr_popup_dialog(best_text))
                else:
                    QTimer.singleShot(0, lambda: self.show_toast(
                        "No text detected - ensure the window is visible.", duration=3000))
            except ImportError:
                QTimer.singleShot(0, lambda: self.show_toast("pytesseract plugin missing: run 'pip install pytesseract'", duration=4000))
            except Exception as ex:
                msg = str(ex)
                if "is not installed" in msg or "tesseract.exe" in msg:
                    QTimer.singleShot(0, lambda: self.show_toast("OCR Engine missing! Install Tesseract-OCR for Windows from GitHub.", duration=6000))
                else:
                    QTimer.singleShot(0, lambda: self.show_toast(f"OCR error: {msg[:80]}", duration=4000))

        threading.Thread(target=_do_ocr, daemon=True).start()

    def _show_ocr_popup_dialog(self, text):
        """Show OCR text in a standard high-visibility popup window."""
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.setWindowTitle("OCR Result")
        msg.setText("Text extracted from image:")
        msg.setInformativeText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setIcon(QMessageBox.Information)
        msg.show()

    def run_qr(self):
        res = self.executor.execute_action({"action": "qr_scanner", "image": self._get_flat()})
        raw = res.get("message", "No result")
        self._show_inline_overlay("QR / Barcode Detected", raw, is_html=True)

    def _show_inline_overlay(self, title, content, is_html=False):
        """Creates a custom overlaid widget on the canvas instead of a dialog window."""
        overlay = QFrame(self.central_frame)
        overlay.setStyleSheet(f"""
            QFrame {{
                background-color: #242424;
                border: 1px solid #444;
                border-radius: 8px;
            }}
        """)
        
        vl = QVBoxLayout(overlay)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(8)
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #FF7A50; font-weight: bold; font-size: 13px; border: none;")
        vl.addWidget(lbl_title)
        
        # Content
        # Use QTextBrowser so that external links correctly open in the browser when clicked
        text_box = QTextBrowser()
        text_box.setOpenExternalLinks(True)
        if is_html:
            text_box.setHtml(content)
        else:
            text_box.setPlainText(content)
            
        text_box.setStyleSheet("""
            QTextBrowser {
                color: #FFFFFF; background: #1A1A1A;
                border: 1px solid #333; border-radius: 6px;
                padding: 8px; font-size: 13px;
            }
        """)
        text_box.setMinimumHeight(60)
        text_box.setMaximumHeight(120)
        vl.addWidget(text_box)
        
        # Buttons
        row = QHBoxLayout()
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(lambda: (__import__('pyperclip').copy(text_box.toPlainText()), self.show_toast("Copied!")))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(overlay.deleteLater)

        for btn in [copy_btn, close_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #3A3A3A; color: #EEE; border: 1px solid #555;
                    border-radius: 5px; padding: 4px 12px; font-weight: bold; font-size: 12px;
                }
                QPushButton:hover { background: #4A4A4A; }
            """)
            
        row.addStretch()
        row.addWidget(copy_btn)
        row.addWidget(close_btn)
        vl.addLayout(row)
        
        # Size and position relative to canvas
        overlay.setFixedWidth(min(400, self.central_frame.width() - 40))
        overlay.adjustSize()
        
        cx = (self.central_frame.width() - overlay.width()) // 2
        cy = (self.central_frame.height() - overlay.height()) // 2
        overlay.move(cx, cy)
        
        # Simple drag to move the overlay
        def mousePress(e):
            overlay._drag_pos = e.globalPos()
        def mouseMove(e):
            if hasattr(overlay, '_drag_pos'):
                delta = e.globalPos() - overlay._drag_pos
                overlay.move(overlay.x() + delta.x(), overlay.y() + delta.y())
                overlay._drag_pos = e.globalPos()
        overlay.mousePressEvent = mousePress
        overlay.mouseMoveEvent = mouseMove
        
        overlay.show()
        overlay.raise_()

    def run_remove_bg(self):
        """Remove background using rembg in a background thread."""
        self.show_toast("Removing background…", duration=60000)
        QApplication.processEvents()
        import threading
        flat = self._get_flat()

        def _do():
            try:
                from rembg import remove as rembg_remove
                result = rembg_remove(flat)
                QTimer.singleShot(0, lambda: self._apply_remove_bg(result))
            except ImportError:
                QTimer.singleShot(0, lambda: self.show_toast(
                    "Install rembg: pip install rembg", duration=4000))
            except Exception as ex:
                msg = str(ex)[:60]
                QTimer.singleShot(0, lambda: self.show_toast(f"BG removal failed: {msg}", duration=4000))

        threading.Thread(target=_do, daemon=True).start()

    def _apply_remove_bg(self, result_img):
        self._tooltip.hide_tip()
        self.image_history.append(self.image.copy())
        self.image_redo.clear()
        
        # Keep transparency layer instead of forcing white bg
        self.image = result_img.convert("RGBA")
        self.canvas.base_pil_image = self.image.copy()
        self.canvas._annotations.clear()
        self.canvas._redraw_annotations()
        self.show_toast("Background removed ✓")

    def run_ask_ai(self):
        """Pass the current snip context data to the main AI chat window."""
        flat = self._get_flat()
        # Merge the new image into context data
        ctx = self.context_data.copy()
        ctx["image"] = flat
        self.ask_ai.emit(ctx)
        # self.close() removed as requested to keep snip open

    def run_pin(self):
        """Pin the current view (with all annotations baked in) to screen."""
        from overlay import PinnedSnip
        from PyQt5.QtWidgets import QDesktopWidget
        flat = self._get_flat()          # <-- includes all edits
        w, h = flat.size
        w = max(w, 50); h = max(h, 50)
        screen = QDesktopWidget().screenGeometry()
        x = screen.width() - w - 20; y = 40
        p = PinnedSnip(flat, (x, y, w, h))
        if hasattr(self.parent_app, "pinned_snips"):
            self.parent_app.pinned_snips.append(p)
        p.show()
        self.show_toast("Pinned to screen! Right-click to dismiss.")


    def moveEvent(self, e):
        super().moveEvent(e)
        if self._palette and self._palette.isVisible():
            self._reposition_palette()

    def closeEvent(self, e):
        if self._tooltip:
            self._tooltip.close()
            self._tooltip.deleteLater()
            self._tooltip = None
        if self._palette:
            self._palette.close()
            self._palette.deleteLater()
            self._palette = None
        super().closeEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(e)

    # ─── Event filter: tooltips + drag ───────────────────────────────────────
    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton) and hasattr(obj, "tool_label") and self._tooltip:
            if event.type() == QEvent.Enter:
                bg = obj.mapToGlobal(QPoint(0, 0))
                scr = QApplication.desktop().screenGeometry()
                self._tooltip._lbl.setText(obj.tool_label)
                self._tooltip._lbl.adjustSize()
                self._tooltip.adjustSize()
                tw = self._tooltip.width(); th = self._tooltip.height()
                ty = bg.y() + (obj.height() - th) // 2
                if bg.x() + obj.width() + 10 + tw > scr.right() - 5:
                    tx = bg.x() - tw - 10
                else:
                    tx = bg.x() + obj.width() + 10
                self._tooltip.show_at(obj.tool_label, QPoint(tx, ty))
            elif event.type() in (QEvent.Leave, QEvent.MouseButtonPress):
                self._tooltip.hide_tip()

        if obj == self.central_frame:
            if event.type() == QEvent.MouseButtonPress:
                self.oldPos = event.globalPos()
                if self._tooltip:
                    self._tooltip.hide_tip()
            elif event.type() == QEvent.MouseMove and getattr(self, "oldPos", None):
                delta = event.globalPos() - self.oldPos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.oldPos = event.globalPos()
        return super().eventFilter(obj, event)
