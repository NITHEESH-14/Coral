import os
import cv2
import mss
import numpy as np
import time
import datetime
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRect, QSize, QPoint
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QSlider
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPixmap
import utils

class DarkSurroundOverlay(QWidget):
    def __init__(self, rect_area):
        super().__init__()
        self.rect_area = rect_area
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.showFullScreen()

    def paintEvent(self, e):
        painter = QPainter(self)
        # Dim exactly like SnippingTool selection
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        # Punch a transparent hole
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect_area, Qt.transparent)

from PyQt5.QtCore import QPointF
import math

from PyQt5.QtCore import QPointF
import math
from capture_suite import get_svg_icon, SVG_ICONS, FloatingTooltip

# Add a cursor icon if missing
if "cursor" not in SVG_ICONS:
    SVG_ICONS["cursor"] = '''<svg viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 3 10 21 13 14 20 17 21 16 14 11 21 4 3 3"></polygon></svg>'''
    
class RecordingBorder(QWidget):
    def __init__(self, rect):
        super().__init__()
        self.setGeometry(rect.adjusted(-2, -2, 2, 2))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.show()

    def paintEvent(self, e):
        painter = QPainter(self)
        pen = QPen(QColor(utils.THEME['primary']))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

class RecordingCanvas(QWidget):
    def __init__(self, rect_area):
        super().__init__()
        self.rect_area = rect_area
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(rect_area)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        self.mode = "none"
        self.current_color = QColor(utils.THEME['primary'])
        self.current_size = 4
        self.annotations = []
        self.redo_stack = []
        self.current_ann = None
        self.drawing = False
        self._blur_cache = {}
        # Background snapshot taken when blur mode is activated
        self._blur_bg_snapshot = None
        self.show()
        self.raise_()

    def set_color(self, hex_str):
        self.current_color = QColor(hex_str)

    def set_size(self, val):
        self.current_size = val

    def undo(self):
        if self.annotations:
            self.redo_stack.append(self.annotations.pop())
            self.update()

    def redo(self):
        if self.redo_stack:
            self.annotations.append(self.redo_stack.pop())
            self.update()

    def set_mode(self, mode):
        self.mode = mode
        if mode == "none":
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setCursor(Qt.CrossCursor)
            
        import ctypes
        import sys
        if sys.platform == 'win32':
            try:
                hwnd = int(self.winId())
                GWL_EXSTYLE = -20
                WS_EX_TRANSPARENT = 0x00000020
                SWP_FRAMECHANGED = 0x0020
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                
                exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                if mode == "none":
                    exstyle |= WS_EX_TRANSPARENT
                else:
                    exstyle &= ~WS_EX_TRANSPARENT
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle)
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER)
            except Exception:
                pass

        # When switching TO blur mode, take a clean background snapshot immediately
        # (canvas is not yet drawing, so the grab is clean)
        if mode == 'blur':
            self._grab_blur_background()
                
        self.raise_()

    def _grab_blur_background(self):
        """Snapshot the recording area right when blur mode is activated — clean, no strokes."""
        from PyQt5.QtWidgets import QApplication
        import time
        # Briefly hide canvas so existing annotations don't bleed into the snapshot
        self.hide()
        QApplication.processEvents()
        time.sleep(0.05)
        screen = QApplication.primaryScreen()
        self._blur_bg_snapshot = screen.grabWindow(
            0,
            self.rect_area.x(), self.rect_area.y(),
            self.rect_area.width(), self.rect_area.height()
        )
        self.show()
        self.raise_()

    def mousePressEvent(self, e):
        if self.mode != "none" and e.button() == Qt.LeftButton:
            self.drawing = True
            self.current_ann = {
                'mode': self.mode, 
                'points': [e.pos()],
                'color': self.current_color,
                'size': self.current_size
            }
            self.annotations.append(self.current_ann)

    def mouseMoveEvent(self, e):
        if self.drawing and self.current_ann:
            self.current_ann['points'].append(e.pos())
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drawing = False
            # When a blur stroke finishes, bake the pixelated snapshot for it
            if self.current_ann and self.current_ann.get('mode') == 'blur':
                self._bake_blur(self.current_ann)
            self.update()

    def _bake_blur(self, ann):
        """Crop and pixelate the pre-captured background snapshot for this stroke's region."""
        pts = ann['points']
        if len(pts) < 1 or self._blur_bg_snapshot is None:
            return
        pen_r = ann['size'] * 4 + 12
        min_x = min(p.x() for p in pts) - pen_r
        min_y = min(p.y() for p in pts) - pen_r
        max_x = max(p.x() for p in pts) + pen_r
        max_y = max(p.y() for p in pts) + pen_r
        local_rect = QRect(int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y))
        local_rect = local_rect.intersected(self.rect())
        if local_rect.isEmpty():
            return
        w, h = local_rect.width(), local_rect.height()
        # Crop from the clean background snapshot (no overlay strokes)
        raw_pix = self._blur_bg_snapshot.copy(local_rect)
        if raw_pix.isNull():
            return
        # Pixelate: downscale to 1/12 → upscale (strong mosaic / censor effect)
        mosaic_w = max(1, w // 12)
        mosaic_h = max(1, h // 12)
        small = raw_pix.scaled(mosaic_w, mosaic_h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        pixelated = small.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        ann['_blur_pix'] = pixelated
        ann['_blur_rect'] = local_rect

    def clear(self):
        self.annotations.clear()
        self.redo_stack.clear()
        self._blur_cache.clear()
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        if self.mode != "none":
            painter.fillRect(self.rect(), QColor(255, 255, 255, 1))
            
        painter.setRenderHint(QPainter.Antialiasing)
        
        for ann in self.annotations:
            pts = ann['points']
            if len(pts) < 1: continue
            
            if ann['mode'] == 'pen':
                pen = QPen(ann['color'])
                pen.setWidth(ann['size'])
                painter.setBrush(Qt.NoBrush)
                if len(pts) > 1:
                    painter.setPen(pen)
                    for i in range(len(pts)-1):
                        painter.drawLine(pts[i], pts[i+1])
                else:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(ann['color'])
                    painter.drawEllipse(pts[0], ann['size']//2, ann['size']//2)
                    
            elif ann['mode'] == 'highlight':
                col = QColor(ann['color'])
                col.setAlpha(120)
                pen = QPen(col)
                pen.setWidth(ann['size'] * 3 + 8)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setBrush(Qt.NoBrush)
                if len(pts) > 1:
                    painter.setPen(pen)
                    for i in range(len(pts)-1):
                        painter.drawLine(pts[i], pts[i+1])
                        
            elif ann['mode'] == 'rect':
                pen = QPen(ann['color'])
                pen.setWidth(ann['size'])
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                if len(pts) > 1:
                    painter.drawRect(QRect(pts[0], pts[-1]).normalized())
                    
            elif ann['mode'] == 'arrow':
                pen = QPen(ann['color'])
                pen.setWidth(ann['size'])
                painter.setPen(pen)
                if len(pts) > 1:
                    p1, p2 = pts[0], pts[-1]
                    painter.drawLine(p1, p2)
                    ang = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
                    arr_sz = max(10, ann['size'] * 3)
                    h1 = QPointF(p2.x() - arr_sz * math.cos(ang - math.pi / 6), p2.y() - arr_sz * math.sin(ang - math.pi / 6))
                    h2 = QPointF(p2.x() - arr_sz * math.cos(ang + math.pi / 6), p2.y() - arr_sz * math.sin(ang + math.pi / 6))
                    painter.drawLine(p2, h1)
                    painter.drawLine(p2, h2)
                    
            elif ann['mode'] == 'blur':
                pen_w = ann['size'] * 4 + 12
                # ── Live preview while drawing (no baked snapshot yet) ──
                if '_blur_pix' not in ann:
                    # Show a semi-transparent dark preview so user can see the path
                    col = QColor(30, 30, 30, 180)
                    pen = QPen(col)
                    pen.setWidth(pen_w)
                    pen.setCapStyle(Qt.RoundCap)
                    pen.setJoinStyle(Qt.RoundJoin)
                    painter.setBrush(Qt.NoBrush)
                    if len(pts) > 1:
                        painter.setPen(pen)
                        for i in range(len(pts) - 1):
                            painter.drawLine(pts[i], pts[i + 1])
                    elif len(pts) == 1:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(col)
                        r = pen_w // 2
                        painter.drawEllipse(pts[0], r, r)
                else:
                    # ── Baked pixelated snapshot ──
                    pix = ann['_blur_pix']
                    rect = ann['_blur_rect']
                    # Clip drawing to the exact stroke shape
                    from PyQt5.QtGui import QPainterPath
                    clip_path = QPainterPath()
                    if len(pts) > 1:
                        # Build a wide stroke path to use as clip mask
                        stroke_pen = QPen(Qt.black, pen_w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                        stroke_path = QPainterPath()
                        stroke_path.moveTo(pts[0])
                        for pt in pts[1:]:
                            stroke_path.lineTo(pt)
                        stroker = __import__('PyQt5.QtGui', fromlist=['QPainterPathStroker']).QPainterPathStroker()
                        stroker.setWidth(pen_w)
                        stroker.setCapStyle(Qt.RoundCap)
                        stroker.setJoinStyle(Qt.RoundJoin)
                        clip_path = stroker.createStroke(stroke_path)
                    else:
                        r = pen_w / 2
                        clip_path.addEllipse(pts[0], r, r)
                    painter.save()
                    painter.setClipPath(clip_path)
                    painter.drawPixmap(rect, pix)
                    painter.restore()

class ScreenRecorderWorker(QThread):
    finished_recording = pyqtSignal(str)
    update_time = pyqtSignal(str)
    
    def __init__(self, rect, fps=20):
        super().__init__()
        self.rect = rect
        self.fps = fps
        self.is_recording = False
        self.output_file = ""
        
    def run(self):
        self.is_recording = True
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = os.path.join(os.getcwd(), "Recordings")
        os.makedirs(save_dir, exist_ok=True)
        self.output_file = os.path.join(save_dir, f"Coral_Recording_{timestamp}.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        
        with mss.mss() as sct:
            monitor = {
                "top": self.rect.y(),
                "left": self.rect.x(),
                "width": self.rect.width(),
                "height": self.rect.height()
            }
            monitor["width"] = max(16, monitor["width"])
            monitor["height"] = max(16, monitor["height"])            
            monitor["width"] -= monitor["width"] % 2
            monitor["height"] -= monitor["height"] % 2
            
            out = cv2.VideoWriter(self.output_file, fourcc, self.fps, (monitor["width"], monitor["height"]))
            
            start_time = time.time()
            frame_duration = 1.0 / self.fps
            
            while self.is_recording:
                loop_start = time.time()
                
                try:
                    sct_img = sct.grab(monitor)
                    img = np.array(sct_img)
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) if hasattr(cv2, 'COLOR_BGRA2BGR') else img[:,:,:3]
                    out.write(frame)
                except Exception as e:
                    import logging
                    logging.error(f"Recording frame error: {e}")
                    try:
                        sct.close()
                        sct = mss.mss()
                    except Exception:
                        pass
                
                try:
                    elapsed = int(time.time() - start_time)
                    mins, secs = divmod(elapsed, 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    if getattr(self, '_last_time', None) != time_str:
                        self.update_time.emit(time_str)
                        self._last_time = time_str
                    
                    elapsed_loop = time.time() - loop_start
                    delay = frame_duration - elapsed_loop
                    if delay > 0:
                        time.sleep(delay)
                except Exception as e:
                    import logging
                    logging.error(f"Recorder timing error: {e}")
                    
            out.release()
            
        self.finished_recording.emit(self.output_file)
        
    def stop(self):
        self.is_recording = False

from PyQt5.QtWidgets import QColorDialog
from capture_suite import PALETTE_COLORS

class RecordingTopPalette(QWidget):
    def __init__(self, rect_area, canvas):
        super().__init__()
        self.canvas = canvas
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        frame = QFrame(self)
        frame.setStyleSheet(f"QFrame {{ background-color: {utils.THEME['surface']}; border: 1px solid #444; border-radius: 12px; }}")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(frame)
        
        inner_v = QVBoxLayout(frame)
        inner_v.setContentsMargins(0, 0, 0, 0)
        inner_v.setSpacing(0)
        
        title_row = QHBoxLayout()
        title_row.setContentsMargins(14, 7, 14, 4)
        lbl = QLabel("✦  Annotation Controls")
        lbl.setStyleSheet("color:#666; font-size:10px; font-weight:bold; letter-spacing:1px;")
        title_row.addWidget(lbl)
        title_row.addStretch()
        self.mode_lbl = QLabel("Pen")
        self.mode_lbl.setStyleSheet("color:#FF7A50; font-weight:bold; font-size:11px; background: #222; padding: 2px 8px; border-radius: 4px; border: 1px solid #FF7A50;")
        title_row.addWidget(self.mode_lbl)
        inner_v.addLayout(title_row)
        
        div = QFrame(); div.setFrameShape(QFrame.HLine); div.setStyleSheet("background:#444; max-height:1px; margin:0;")
        inner_v.addWidget(div)
        
        row = QHBoxLayout()
        row.setContentsMargins(12, 6, 12, 8)
        row.setSpacing(10)
        
        self.size_lbl = QLabel("Size: 4")
        self.size_lbl.setStyleSheet("color:#AAA; font-size:11px; min-width:52px;")
        row.addWidget(self.size_lbl)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 40)
        self.slider.setValue(4)
        self.slider.setFixedWidth(110)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height:4px; background:#444; border-radius:2px; }}
            QSlider::handle:horizontal {{ background:{utils.THEME['primary']}; width:14px; height:14px; margin:-5px 0; border-radius:7px; }}
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
            btn.setStyleSheet(f"QPushButton {{ background:{c}; border:2px solid #555; border-radius:10px; }} QPushButton:hover {{ border:2px solid #FFF; }}")
            btn.clicked.connect(lambda _, col=c: self.canvas.set_color(col))
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
            
        inner_v.addLayout(row)
        self.adjustSize()
        x = rect_area.x() + (rect_area.width() - self.width()) // 2
        y = max(0, rect_area.top() - self.height() - 15)
        self.move(x, y)
        self.show()
        self.raise_()

    def _open_color_picker(self):
        color = QColorDialog.getColor(Qt.white, self, "Pick a Color")
        if color.isValid():
            self.canvas.set_color(color.name())

    def set_mode(self, label, show_colors=True):
        if not show_colors:
            self.hide()
            return
        self.mode_lbl.setText(label)
        self.color_sep.setVisible(show_colors)
        self.picker_btn.setVisible(show_colors)
        for btn in self.color_btns:
            btn.setVisible(show_colors)
        self.adjustSize()
        self.show()

    def _on_size(self, val):
        self.size_lbl.setText(f"Size: {val}")
        self.canvas.set_size(val)

class RecordingToolPanel(QWidget):
    def __init__(self, rect_area, top_palette, canvas):
        super().__init__()
        self.canvas = canvas
        self.top_palette = top_palette
        self._tooltip = FloatingTooltip()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        frame = QFrame(self)
        frame.setStyleSheet(f"QFrame {{ background-color: {utils.THEME['background']}; border: 1px solid #444; border-radius: 12px; }}")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(6)

        def add_group(name):
            lbl = QLabel(name)
            lbl.setStyleSheet("color:#555; font-size:9px; font-weight:bold; letter-spacing:1px; margin-top:4px; margin-bottom: 2px;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        self.btns = {}

        def add_row(w1, w2=None):
            row = QHBoxLayout()
            row.setSpacing(4)
            row.addWidget(w1)
            if w2:
                row.addWidget(w2)
            else:
                dummy = QWidget(); dummy.setFixedSize(36, 36)
                row.addWidget(dummy)
            layout.addLayout(row)

        add_group("ACTIONS")
        undo_b = self.create_custom_btn("undo", self.canvas.undo, "#6B3300", "#7B4000", "Undo")
        redo_b = self.create_custom_btn("redo", self.canvas.redo, "#3A2800", "#4A3500", "Redo")
        add_row(undo_b, redo_b)

        add_group("DRAW")
        add_row(self.create_tool_btn("draw", "pen", "Pen"),
                self.create_tool_btn("highlight", "highlight", "Highlighter"))

        add_group("SHAPES")
        add_row(self.create_tool_btn("arrow", "arrow", "Arrow"),
                self.create_tool_btn("rect", "rect", "Rectangle"))

        add_group("ANNOTATE")
        add_row(self.create_tool_btn("blur", "blur", "Blur Brush"),
                self.create_tool_btn("cursor", "none", "Pointer"))

        self.btns['none'].setChecked(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(frame)

        self.adjustSize()
        x = rect_area.right() + 15
        y = max(0, rect_area.y() + (rect_area.height() - self.height()) // 2)

        # Collision resolution against top_palette
        if hasattr(self, 'top_palette') and self.top_palette:
            tp_geo = self.top_palette.geometry()
            if x < tp_geo.right() + 15:
                y = max(y, tp_geo.bottom() + 15)

        from PyQt5.QtWidgets import QApplication
        screen_geo = QApplication.primaryScreen().geometry()
        if x + self.width() > screen_geo.right():
            x = rect_area.right() - self.width() - 15

        self.move(x, y)
        self.show()
        self.raise_()

    def create_custom_btn(self, svg_key, fn, bg, hov, tip):
        b = QPushButton()
        b.setFixedSize(36, 36)
        b.setIcon(get_svg_icon(svg_key))
        b.setIconSize(QSize(18, 18))
        b.setStyleSheet(f"""
            QPushButton {{ background-color: {bg}; border: 1px solid #555; border-radius: 8px; }}
            QPushButton:hover {{ background-color: {hov}; border: 1px solid {utils.THEME['primary']}; }}
        """)
        b.tool_label = tip
        b.installEventFilter(self)
        b.clicked.connect(fn)
        return b

    def create_tool_btn(self, svg_key, mode, tip):
        b = QPushButton()
        b.setFixedSize(36, 36)
        b.setIcon(get_svg_icon(svg_key))
        b.setIconSize(QSize(18, 18))
        b.setStyleSheet(f"""
            QPushButton {{ background-color: {utils.THEME['surface']}; border: 1px solid #555; border-radius: 8px; }}
            QPushButton:hover {{ background-color: #444; border: 1px solid {utils.THEME['primary']}; }}
            QPushButton:checked {{ background-color: #252525; border: 2px solid {utils.THEME['primary']}; }}
        """)
        b.tool_label = tip
        b.setCheckable(True)
        b.installEventFilter(self)
        b.clicked.connect(lambda ch, m=mode: self.set_tool(m))
        self.btns[mode] = b
        return b

    # ── Tooltip: use Qt's built-in QToolTip (always works inside FramelessWindowHint) ──
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        from PyQt5.QtWidgets import QToolTip, QApplication
        if isinstance(obj, QPushButton) and hasattr(obj, 'tool_label'):
            if event.type() == QEvent.Enter:
                gpos = obj.mapToGlobal(QPoint(obj.width() + 6, obj.height() // 2))
                QToolTip.showText(gpos, obj.tool_label, obj)
            elif event.type() == QEvent.Leave:
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def set_tool(self, mode):
        for m, b in self.btns.items():
            b.setChecked(m == mode)
        self.canvas.set_mode(mode)
        title_map = {
            'pen': 'Pen', 'highlight': 'Highlighter',
            'rect': 'Rectangle', 'arrow': 'Arrow',
            'blur': 'Blur Brush', 'none': 'Pointer',
        }
        title = title_map.get(mode, 'Pen')
        self.top_palette.set_mode(title, mode not in ('none', 'blur'))


class RecordingControlPanel(QWidget):
    recording_finished = pyqtSignal(str)
    closed = pyqtSignal()
    
    def __init__(self, rect_area):
        super().__init__()
        self.rect_area = rect_area
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.border_outline = RecordingBorder(rect_area)
        self.canvas = RecordingCanvas(rect_area)
        self.surround = DarkSurroundOverlay(rect_area)
        
        self.top_palette = RecordingTopPalette(rect_area, self.canvas)
        self.tool_panel = RecordingToolPanel(rect_area, self.top_palette, self.canvas)
        
        self.frame = QFrame(self)
        self.frame.setStyleSheet(f"QFrame {{ background-color: {utils.THEME['background']}; border: 1px solid #444; border-radius: 8px; }}")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.frame)
        
        row = QHBoxLayout(self.frame)
        row.setContentsMargins(12, 6, 12, 6)
        row.setSpacing(10)
        
        self.time_lbl = QLabel("00:00")
        self.time_lbl.setStyleSheet(f"color: {utils.THEME['primary']}; font-weight:bold; font-size:12px; margin-right:5px;")
        row.addWidget(self.time_lbl)
        
        sep = QFrame(); sep.setFrameShape(QFrame.VLine); sep.setStyleSheet("border-left: 1px solid #444; max-width: 1px;")
        row.addWidget(sep)
        
        self.record_btn = QPushButton("● Record")
        self.record_btn.setStyleSheet(f"QPushButton {{ background-color: #FF4444; color: white; border-radius: 4px; padding: 4px 12px; font-weight: bold; font-size: 11px; }} QPushButton:hover {{ background-color: #FF6666; }} QPushButton:disabled {{ background-color: #666; color: #AAA; }}")
        self.record_btn.clicked.connect(self.start_recording)
        row.addWidget(self.record_btn)
        
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"QPushButton {{ background-color: {utils.THEME['surface']}; color: {utils.THEME['primary']}; border: 1px solid {utils.THEME['primary']}; border-radius: 4px; padding: 4px 12px; font-weight: bold; font-size: 11px; }} QPushButton:hover {{ background-color: #444; }} QPushButton:disabled {{ border: 1px solid #555; color: #555; }}")
        self.stop_btn.clicked.connect(self.stop_recording)
        row.addWidget(self.stop_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #AAA; font-size: 14px; border: none; padding: 4px; } QPushButton:hover { color: #FFF; }")
        self.close_btn.clicked.connect(self.close_panel)
        row.addWidget(self.close_btn)
        
        self.worker = None
        
        self.adjustSize()
        x = rect_area.x() + (rect_area.width() - self.width()) // 2
        
        from PyQt5.QtWidgets import QApplication
        screen_geo = QApplication.primaryScreen().geometry()
        y_target = rect_area.bottom() + 15
        
        # Prevent it from going entirely off screen
        if y_target + self.height() > screen_geo.bottom():
            y_target = screen_geo.bottom() - self.height() - 10
            
        self.move(x, y_target)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def start_recording(self):
        self.record_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        
        self.worker = ScreenRecorderWorker(self.rect_area)
        self.worker.update_time.connect(self.time_lbl.setText)
        self.worker.finished_recording.connect(self.on_recording_finished)
        self.worker.start()

    def stop_recording(self):
        if self.worker:
            self.stop_btn.setEnabled(False)
            self.worker.stop()
            self.time_lbl.setText("Saving...")

    def on_recording_finished(self, path):
        self.recording_finished.emit(path)
        self.close_panel()

    def close_panel(self):
        # Stop any running recording worker before tearing down widgets
        if hasattr(self, 'worker') and self.worker:
            try:
                self.worker.stop()
                self.worker.wait(3000)  # Wait up to 3s for clean shutdown
            except Exception:
                pass
            self.worker = None

        if self.canvas:
            self.canvas.close()
            self.canvas.deleteLater()
            self.canvas = None
        if hasattr(self, 'border_outline') and self.border_outline:
            self.border_outline.close()
            self.border_outline.deleteLater()
            self.border_outline = None
        if hasattr(self, 'surround') and self.surround:
            self.surround.close()
            self.surround.deleteLater()
            self.surround = None
        if hasattr(self, 'top_palette') and self.top_palette:
            self.top_palette.close()
            self.top_palette.deleteLater()
            self.top_palette = None
        if hasattr(self, 'tool_panel') and self.tool_panel:
            self.tool_panel.close()
            self.tool_panel.deleteLater()
            self.tool_panel = None
        self.closed.emit()
        self.close()
