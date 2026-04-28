"""
ui_scraper.py — Structural UI Perception Layer for Coral

Uses Windows UI Automation (UIA) via pywinauto to query the accessibility tree
for every interactable element inside a snip region.  Returns a compact JSON
manifest that the LLM can reason over instead of (or alongside) OCR text.

Key capabilities:
  - scrape_region(x, y, w, h) → list of element dicts
  - get_window_info(hwnd)      → app name, title, class
  - detect_explorer_path(hwnd) → resolved filesystem path for File Explorer
"""

import sys
import os
import warnings

sys.coinit_flags = 2  # STA — must match PyQt5's threading model

import win32gui
import utils

logger = utils.setup_logger(__name__)

# ── Lazy pywinauto imports (suppress the noisy deprecation warnings) ──────────
_uia_app = None

def _lazy_uia():
    """Import pywinauto once and cache the module references."""
    global _uia_app
    if _uia_app is not None:
        return _uia_app
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from pywinauto import Desktop
    _uia_app = Desktop(backend="uia")
    return _uia_app


# ─── Public API ───────────────────────────────────────────────────────────────

def scrape_region(x: int, y: int, w: int, h: int, max_depth: int = 8, max_elements: int = 120) -> dict:
    """
    Walk the UIA tree for every top-level window that overlaps the snip region
    and collect all interactable elements whose bounding-rect intersects (x,y,w,h).

    Returns
    -------
    dict with keys:
        "window"     – info about the foreground window under the snip center
        "elements"   – list of element dicts (role, name, value, rect, states …)
        "explorer_path" – resolved filesystem path if the window is File Explorer, else ""
        "has_ui_data"  – True if any elements were found (used to decide OCR fallback)
    """
    result = {
        "window": {},
        "elements": [],
        "explorer_path": "",
        "has_ui_data": False,
    }

    # 1. Identify the window under the center of the snip
    cx, cy = x + w // 2, y + h // 2
    hwnd = win32gui.WindowFromPoint((cx, cy))

    # Walk up to the top-level parent
    while True:
        parent = win32gui.GetParent(hwnd)
        if not parent:
            break
        hwnd = parent

    result["window"] = _get_window_info(hwnd)

    # 2. Try to resolve File-Explorer path (fast COM path first)
    class_name = win32gui.GetClassName(hwnd)
    if class_name == "CabinetWClass":
        result["explorer_path"] = _detect_explorer_path_fast(hwnd)
    elif class_name in ("Progman", "WorkerW"):
        result["explorer_path"] = os.path.join(os.path.expanduser("~"), "Desktop")

    # 3. Scrape the UIA tree for elements inside the region
    try:
        elements = _collect_elements(hwnd, x, y, w, h, max_depth, max_elements)
        result["elements"] = elements
        result["has_ui_data"] = len(elements) > 0
    except Exception as e:
        logger.warning(f"UIA scrape failed: {e}")

    return result


def get_element_summary(scrape_result: dict, max_chars: int = 3000) -> str:
    """
    Convert the raw scrape result into a compact, LLM-friendly text summary.
    Prioritises buttons, edits, and text controls — skips decorative containers.
    """
    lines = []

    win = scrape_result.get("window", {})
    if win:
        lines.append(f"[Window] {win.get('app', '?')} — \"{win.get('title', '')}\"")

    explorer_path = scrape_result.get("explorer_path", "")
    if explorer_path:
        lines.append(f"[Explorer Path] {explorer_path}")

    elements = scrape_result.get("elements", [])
    if not elements:
        lines.append("[No accessible UI elements found in region]")
        return "\n".join(lines)

    lines.append(f"[{len(elements)} UI elements in snip region]")

    for el in elements:
        role = el.get("role", "Unknown")
        name = el.get("name", "")
        value = el.get("value", "")
        states = el.get("states", [])

        parts = [f"  {role}"]
        if name:
            parts.append(f'"{name}"')
        if value:
            parts.append(f'val="{value}"')
        if states:
            parts.append(f"({', '.join(states)})")

        line = " ".join(parts)
        lines.append(line)

        # Budget guard
        if sum(len(l) for l in lines) > max_chars:
            lines.append(f"  … ({len(elements) - len(lines) + 3} more elements)")
            break

    return "\n".join(lines)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _get_window_info(hwnd: int) -> dict:
    """Return basic info about a window handle."""
    try:
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        # Extract process name
        import win32process, psutil
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            app_name = proc.name()
        except Exception:
            app_name = ""
        return {"hwnd": hwnd, "title": title, "class": cls, "app": app_name, "pid": pid}
    except Exception as e:
        logger.debug(f"_get_window_info error: {e}")
        return {"hwnd": hwnd, "title": "", "class": "", "app": "", "pid": 0}


def _detect_explorer_path_fast(hwnd: int) -> str:
    """
    Resolve the filesystem path for a File-Explorer window using
    Shell.Application COM — the fastest and most reliable method.
    Falls back to pywinauto address-bar scrape.
    """
    try:
        import win32com.client
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
            if int(window.HWND) == int(hwnd):
                path = window.Document.Folder.Self.Path
                if os.path.exists(path):
                    return path
    except Exception as e:
        logger.debug(f"COM explorer-path failed: {e}")

    # Fallback: pywinauto address bar
    try:
        from pywinauto import Application
        app = Application(backend="uia").connect(handle=hwnd)
        window = app.window(handle=hwnd)
        address_bar = window.child_window(auto_id="1001", control_type="ToolBar")
        if address_bar.exists(timeout=0.3):
            val = address_bar.window_text()
            if val.startswith("Address: "):
                path = val[9:].strip()
                if os.path.exists(path):
                    return path
    except Exception as e:
        logger.debug(f"pywinauto address-bar fallback failed: {e}")

    return ""


def _rect_intersects(el_rect, region):
    """Check if an element's bounding rect intersects the snip region."""
    rx, ry, rw, rh = region
    r_right = rx + rw
    r_bottom = ry + rh

    try:
        el_left = el_rect.left
        el_top = el_rect.top
        el_right = el_rect.right
        el_bottom = el_rect.bottom
    except AttributeError:
        return False

    if el_right <= rx or el_left >= r_right:
        return False
    if el_bottom <= ry or el_top >= r_bottom:
        return False
    return True


# Roles we care about (skip decorative panes/groups to reduce noise)
_INTERESTING_ROLES = {
    "Button", "Edit", "Text", "CheckBox", "RadioButton",
    "ComboBox", "ListItem", "MenuItem", "TabItem", "TreeItem",
    "Hyperlink", "Image", "ToolBar", "StatusBar", "Slider",
    "ProgressBar", "DataItem", "Header", "HeaderItem",
    "List", "Menu", "MenuBar", "Tab", "TitleBar", "ToolTip",
    "Document", "ScrollBar",
}


def _collect_elements(hwnd, x, y, w, h, max_depth, max_elements):
    """
    Recursively walk the UIA tree rooted at *hwnd* and collect every
    element whose bounding rect intersects the snip region.
    """
    elements = []
    region = (x, y, w, h)

    try:
        from pywinauto import Application
        app = Application(backend="uia").connect(handle=hwnd)
        root = app.window(handle=hwnd).wrapper_object()
    except Exception as e:
        logger.debug(f"Cannot connect to hwnd {hwnd}: {e}")
        return elements

    def _walk(element, depth):
        if depth > max_depth or len(elements) >= max_elements:
            return

        try:
            rect = element.rectangle()
        except Exception:
            return

        if not _rect_intersects(rect, region):
            return

        # Get properties
        try:
            role = element.element_info.control_type or "Unknown"
        except Exception:
            role = "Unknown"

        try:
            name = (element.element_info.name or "").strip()
        except Exception:
            name = ""

        # Only collect "interesting" roles or elements that have a name
        if role in _INTERESTING_ROLES or name:
            entry = {
                "role": role,
                "name": name[:200],  # cap very long names
                "rect": {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                },
            }

            # Value (e.g. text content of an Edit control)
            try:
                from pywinauto.controls.uiawrapper import UIAWrapper
                iface = element.iface_value
                if iface:
                    val = iface.CurrentValue
                    if val:
                        entry["value"] = str(val)[:300]
            except Exception:
                pass

            # States
            states = []
            try:
                if not element.is_enabled():
                    states.append("disabled")
            except Exception:
                pass
            try:
                if hasattr(element, "get_toggle_state"):
                    ts = element.get_toggle_state()
                    states.append("checked" if ts == 1 else "unchecked")
            except Exception:
                pass
            if states:
                entry["states"] = states

            elements.append(entry)

        # Recurse into children
        try:
            children = element.children()
        except Exception:
            children = []

        for child in children:
            if len(elements) >= max_elements:
                break
            _walk(child, depth + 1)

    _walk(root, 0)
    return elements
