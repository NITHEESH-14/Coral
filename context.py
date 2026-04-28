import datetime
import os
import sys
sys.coinit_flags = 2  # Match PyQt5's STA threading model to prevent OleInitialize warning

import win32gui
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    import pywinauto
from pywinauto import Application
from PIL import ImageGrab
import utils

logger = utils.setup_logger(__name__)

def capture_context(region) -> dict:
    """
    Captures the OS context at the snipped region.
    region is a tuple (x, y, w, h)
    Returns a dict with context_type, path, items, etc.

    NEW: Also runs the UIA scraper to provide structural UI data when available.
    The scraper's resolved explorer_path takes priority over the legacy path
    detection, making "create folder at snip location" work reliably.
    """
    x, y, w, h = region
    
    if w <= 0: w = 1
    if h <= 0: h = 1
    
    try:
        # Take screenshot of the region, utilizing all screens for multi-monitor support
        image = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    except Exception as e:
        logger.error(f"ImageGrab failed: {e}")
        image = None
    
    # Find window under the center of the snip region
    center_x = x + w // 2
    center_y = y + h // 2
    hwnd = win32gui.WindowFromPoint((center_x, center_y))
    
    # Get the top-level parent window
    while True:
        parent = win32gui.GetParent(hwnd)
        if not parent:
            break
        hwnd = parent

    class_name = win32gui.GetClassName(hwnd)
    
    context_type = "unknown_app"
    path = ""
    items = []
    
    # ── UIA Structural Scrape ─────────────────────────────────────────────
    ui_data = None
    ui_summary = ""
    try:
        from ui_scraper import scrape_region, get_element_summary
        ui_data = scrape_region(x, y, w, h)
        ui_summary = get_element_summary(ui_data)
        logger.debug(f"UIA scrape: {len(ui_data.get('elements', []))} elements found")
    except Exception as e:
        logger.warning(f"UIA scrape failed (will fall back to OCR): {e}")
        ui_data = {"elements": [], "explorer_path": "", "has_ui_data": False, "window": {}}

    # ── Path detection (prefer UIA result) ────────────────────────────────
    # The scraper already resolves Explorer paths via COM + address-bar,
    # so we trust it first.
    if ui_data and ui_data.get("explorer_path"):
        path = ui_data["explorer_path"]
        if class_name in ("Progman", "WorkerW"):
            context_type = "desktop"
        else:
            context_type = "file_explorer"
        items = _get_folder_items(path)
    elif class_name in ("Progman", "WorkerW"):
        context_type = "desktop"
        path = os.path.join(os.path.expanduser("~"), "Desktop")
        items = _get_folder_items(path)
    elif class_name == "CabinetWClass":
        context_type = "file_explorer"
        path = _get_explorer_path(hwnd)
        if path:
            items = _get_folder_items(path)
        else:
            context_type = "unknown_app"
    
    # Fallback: if we couldn't detect a path, default to Desktop
    if not path:
        path = os.path.join(os.path.expanduser("~"), "Desktop")
        items = _get_folder_items(path)
        if context_type == "unknown_app":
            context_type = "desktop"

    # Calculate relative coordinates so we can track the region even if the window moves
    try:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        rel_x = x - left
        rel_y = y - top
    except Exception:
        rel_x, rel_y = 0, 0

    snapshot = {
        "captured_at": datetime.datetime.now().isoformat(),
        "context_type": context_type,
        "region": {"x": x, "y": y, "w": w, "h": h},
        "path": path,
        "items": items,
        "hwnd": hwnd,
        "rel_x": rel_x,
        "rel_y": rel_y,
        "image": image, # Add image object for the popup to use (won't be sent to Groq)

        # ── Structural UI data (new) ──────────────────────────────────────
        "ui_elements": ui_data.get("elements", []) if ui_data else [],
        "ui_summary": ui_summary,
        "has_ui_data": ui_data.get("has_ui_data", False) if ui_data else False,
        "window_info": ui_data.get("window", {}) if ui_data else {},
    }
    
    logger.debug(f"Captured context: {snapshot['context_type']} at {snapshot['path']} "
                 f"(UIA: {len(snapshot['ui_elements'])} elements)")
    return snapshot

def _get_folder_items(path: str) -> list:
    items = []
    try:
        for entry in os.scandir(path):
            items.append({
                "name": entry.name,
                "type": "folder" if entry.is_dir() else "file"
            })
    except Exception as e:
        logger.error(f"Error reading folder items: {e}")
    return items

import win32com.client

def _get_explorer_path(hwnd) -> str:
    """
    Attempts to get the current path from a File Explorer window
    using the robust Shell.Application COM interface.
    """
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
            # Check if this shell window matches the handle we are hovering over
            if int(window.HWND) == int(hwnd):
                path = window.Document.Folder.Self.Path
                if os.path.exists(path):
                    return path
                    
        # If the direct match fails, try pywinauto as a last fallback
        app = Application(backend="uia").connect(handle=hwnd)
        window = app.window(handle=hwnd)
        address_bar = window.child_window(auto_id="1001", control_type="ToolBar")
        if address_bar.exists():
            val = address_bar.window_text()
            if val.startswith("Address: "):
                path = val[9:].strip()
                if os.path.exists(path):
                    return path
    except Exception as e:
        logger.error(f"Failed to extract path from Explorer: {e}")
    return ""
