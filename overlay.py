from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, pyqtSignal, pyqtSlot, QMetaObject
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush

class SelectionOverlay(QWidget):
    # Emits (x, y, w, h)
    snip_completed = pyqtSignal(tuple)

    def __init__(self, callback=None):
        super().__init__()
        if callback:
            self.snip_completed.connect(callback)
            
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.start_pos = None
        self.current_pos = None
        self.is_drawing = False

    def showEvent(self, event):
        super().showEvent(event)
        self.grabKeyboard()
        self.activateWindow()
        self.setFocus()

    @pyqtSlot()
    def hide_overlay(self):
        self.releaseKeyboard()
        self.hide()
        self.close()
        
        if getattr(self, 'is_drawing', False) == False:
            try:
                import utils, win32gui
                if hasattr(utils, 'PREV_HWND') and utils.PREV_HWND:
                    win32gui.SetForegroundWindow(utils.PREV_HWND)
            except: pass

    def closeEvent(self, event):
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = self.start_pos
            self.is_drawing = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.current_pos = event.pos()
            self.update()
            
            # Calculate coordinates
            rect = QRect(self.start_pos, self.current_pos).normalized()
            
            # Hide overlay and emit signal
            self.hide_overlay()
            self.snip_completed.emit((rect.x(), rect.y(), rect.width(), rect.height()))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_overlay()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Fill whole screen with a semi-transparent dark overlay
        overlay_color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay_color)

        if self.is_drawing and self.start_pos and self.current_pos:
            # Cut out the selection area
            rect = QRect(self.start_pos, self.current_pos).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            # Draw border around selection
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(255, 127, 80)) # Coral color
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(rect)

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QPoint, Qt

class PinnedSnip(QWidget):
    def __init__(self, pil_image, region, is_live=False, context=None):
        super().__init__()
        self.source_region = region
        self.is_live = is_live
        self.tracking_context = context
        self.hThumb = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Convert PIL to QPixmap
        img = pil_image.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimage = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
        self.pixmap = QPixmap.fromImage(qimage)
        
        self.label = QLabel(self)
        self.label.setPixmap(self.pixmap)
        
        if self.is_live:
            # Green border to indicate it's a live "Living Snip"
            self.label.setStyleSheet("border: 2px solid #50FF7A; border-radius: 4px;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.setGeometry(region[0], region[1], region[2], region[3])
        self.show()
        
        # Tell Windows 10/11 DWM to make this specific window completely invisible to screen captures!
        # This completely cures the "infinite tunnel" Droste effect without needing to flicker the UI.
        try:
            import ctypes
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception as e:
            print(f"Could not set display affinity: {e}")
        
        self.oldPos = self.pos()
        
        if self.is_live and self.tracking_context and self.tracking_context.get("hwnd"):
            # Enable hardware-accelerated 60 FPS GPU streaming via Windows DWM
            try:
                import ctypes
                from ctypes.wintypes import DWORD, RECT, BOOL
                
                class DWM_THUMBNAIL_PROPERTIES(ctypes.Structure):
                    _fields_ = [
                        ("dwFlags", DWORD),
                        ("rcDestination", RECT),
                        ("rcSource", RECT),
                        ("opacity", ctypes.c_byte),
                        ("fVisible", BOOL),
                        ("fSourceClientAreaOnly", BOOL),
                    ]
                
                src_hwnd = self.tracking_context["hwnd"]
                dest_hwnd = int(self.winId())
                
                self.hThumb = ctypes.c_void_p()
                ctypes.windll.dwmapi.DwmRegisterThumbnail(dest_hwnd, src_hwnd, ctypes.byref(self.hThumb))
                
                rx = self.tracking_context.get("rel_x", 0)
                ry = self.tracking_context.get("rel_y", 0)
                w = self.source_region[2]
                h = self.source_region[3]
                
                props = DWM_THUMBNAIL_PROPERTIES()
                # Flags: Dest Rect (1) | Source Rect (2) | Visible (8)
                props.dwFlags = 0x01 | 0x02 | 0x08
                
                # DWM renders exactly into the bounds of our widget.
                # We offset it by 2px inward on all sides so it perfectly sits *inside* the 2px PyQt green border!
                props.rcDestination = RECT(2, 2, w - 2, h - 2)
                
                # We crop the exact snippet region out of the source app's live buffer
                props.rcSource = RECT(rx, ry, rx + w, ry + h)
                
                props.fVisible = True
                ctypes.windll.dwmapi.DwmUpdateThumbnailProperties(self.hThumb, ctypes.byref(props))
            except Exception as e:
                print(f"DWM Live stream failed: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Delete:
            self.close()

    def closeEvent(self, event):
        if self.hThumb is not None:
            import ctypes
            ctypes.windll.dwmapi.DwmUnregisterThumbnail(self.hThumb)
        super().closeEvent(event)
            
    def contextMenuEvent(self, event):
        # Allow closing via right click
        self.close()
