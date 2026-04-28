# 🪸 Coral — Agentic Desktop Assistant

> A locally-running, AI-powered desktop automation agent for Windows that understands what's on your screen and acts on it.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
5. [Global Hotkeys](#global-hotkeys)
6. [Interaction Modes](#interaction-modes)
7. [Capture Suite](#capture-suite)
8. [Slash Commands Reference](#slash-commands-reference)
9. [System Automation](#system-automation)
10. [Macro Recorder (Offline RPA)](#macro-recorder-offline-rpa)
11. [Vault (Persistent Memory)](#vault-persistent-memory)
12. [Settings & Configuration](#settings--configuration)
13. [Living Snips](#living-snips)
14. [Screen Recorder](#screen-recorder)
15. [File Structure](#file-structure)

---

## Overview

Coral is a **standalone background agent** that runs in the Windows system tray. It uses screen-snipping to understand the user's current OS context (which folder is open, what files are visible) and accepts **plain English commands** or **slash commands** to perform file operations, system automation, image processing, and more — all without switching applications.

### Key Principles

- **Context-Aware** — Coral reads the active Explorer window, desktop, or any app under the snip region to understand *where* you are.
- **Agentic Execution** — AI interprets your intent and generates structured actions that are executed locally. No cloud file access.
- **Reversible** — Most file operations support **Undo** via the built-in undo stack.
- **Offline-First** — All execution happens locally. Only AI inference calls the cloud (Groq/Gemini API).

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    System Tray (pystray)                │
│                    ┌─────────┐                         │
│                    │  Coral   │  ← Background Agent     │
│                    └────┬────┘                         │
│                         │                              │
│         ┌───────────────┼───────────────┐              │
│         ▼               ▼               ▼              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │ Snip Mode  │  │Global Mode │  │Record Mode │       │
│  │ Ctrl+Sh+S  │  │ Ctrl+Sh+G  │  │ Ctrl+Sh+X  │       │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘       │
│        │               │               │              │
│        ▼               ▼               ▼              │
│  SelectionOverlay (fullscreen, semi-transparent)       │
│        │               │               │              │
│        ▼               ▼               ▼              │
│  CaptureSuite    ChatPopup       RecordingPanel        │
│  (annotate,      (AI chat,       (record screen        │
│   OCR, pin)       commands)       region as MP4)       │
│        │               │                              │
│        ▼               ▼                              │
│  ┌──────────────────────────┐                         │
│  │     ActionExecutor       │ ← 40+ local actions     │
│  │     UndoManager          │ ← reversible stack      │
│  │     TagManager           │ ← file tagging          │
│  │     EverythingAPI        │ ← system-wide search    │
│  └──────────────────────────┘                         │
│        │                                              │
│        ▼                                              │
│  ┌──────────────────────────┐                         │
│  │  AI Client (Groq/Gemini) │ ← intent recognition   │
│  └──────────────────────────┘                         │
└────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Hotkey** → Captured by `keyboard` library from any app
2. **Overlay** → Fullscreen semi-transparent PyQt5 widget, user drags a rectangle
3. **Context Capture** → `context.py` screenshots the region, detects the window class via Win32 API, reads the Explorer path via COM `Shell.Application`
4. **Popup** → Presents the captured context to the user; accepts natural language or slash commands
5. **AI Inference** → Sends context + user text to Groq (Llama 3.3 70B) or Gemini Flash → returns structured JSON action
6. **Execution** → `ActionExecutor` performs the action locally (file ops, system calls, image processing)
7. **Undo** → Reverse action pushed to `UndoManager` stack

---

## Tech Stack

### Core Framework

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **GUI** | PyQt5 | All windows, overlays, popups, and widgets |
| **System Tray** | pystray + Pillow | Background agent with tray icon |
| **Hotkeys** | keyboard | Global hotkey capture from any application |
| **Event Loop** | QApplication (Qt) | Main event loop; supports signals/slots for thread-safe UI updates |

### AI & Intelligence

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary LLM** | Groq API (Llama 3.3 70B Versatile) | Natural language → structured JSON action translation |
| **Alternative LLM** | Google Gemini 1.5 Flash | Native vision support for image+text understanding |
| **OCR Engine** | pytesseract (Tesseract OCR) | Extract text from screen snips for AI context and `/extract` command |
| **Prompt Engineering** | System prompt with action schema | LLM returns `{"message": "...", "action_json": {...}}` — always valid JSON |

### Windows Integration

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Window Detection** | pywin32 (win32gui) | Identify the window under the snip region, get foreground window handle |
| **Explorer Path** | win32com.client (Shell.Application COM) | Extract the current folder path from File Explorer windows |
| **UI Automation** | pywinauto | Fallback address-bar reading from Explorer |
| **File Search** | Everything SDK (Everything64.dll) | Instant system-wide file search via C DLL bindings (ctypes) |
| **DWM Integration** | ctypes → dwmapi.dll | Living Snips use DWM Thumbnail API for 60 FPS hardware-accelerated live previews |
| **Focus Management** | ctypes → user32.dll | `SetForegroundWindow` + `AttachThreadInput` for reliable focus stealing |
| **Display Affinity** | ctypes → user32.dll | `SetWindowDisplayAffinity` to exclude pinned snips from screen captures (prevents infinite recursion) |

### File & Image Processing

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Image Capture** | Pillow (ImageGrab) | Screenshot region capture, multi-monitor support |
| **Image Processing** | Pillow (ImageFilter, quantize) | Blur, color extraction, format conversion |
| **Background Removal** | rembg | AI-powered background removal from snips |
| **QR/Barcode** | pyzbar | Decode QR codes and barcodes from screen snips |
| **Screen Recording** | OpenCV (cv2) + threading | Record screen regions as MP4 video files |

### System Control

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Volume Control** | pycaw (Windows Core Audio) | Set/mute system volume |
| **Process Management** | psutil | Kill applications, get system info (CPU, RAM, battery) |
| **Power Management** | ctypes → PowrProf.dll | Lock, sleep, hibernate the workstation |
| **Dark Mode** | winreg (Registry) | Toggle Windows dark mode via registry |
| **Recycle Bin** | send2trash + Shell COM | Safe delete to recycle bin, and restore from it |
| **Shortcuts** | win32com.client (WScript.Shell) | Create Windows `.lnk` shortcut files |
| **Wallpaper** | ctypes → user32.dll | Set desktop wallpaper from snipped image |
| **Clipboard** | pyperclip + QApplication.clipboard() | Auto-copy results, clipboard watcher for scratchpad |

### Macro System

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Input Recording** | pynput (mouse + keyboard listeners) | Record mouse movements, clicks, and keypresses with timestamps |
| **Input Replay** | pynput (mouse + keyboard controllers) | Replay recorded events with timing preservation |
| **Storage** | JSON files in `macros/` directory | Each macro saved as timestamped event array |

---

## Getting Started

### Prerequisites

- **Windows 10/11**
- **Python 3.9+**
- **Everything** search tool running (for system-wide file search)
- **Tesseract OCR** installed (for text extraction from screen)

### Installation

```bash
# Clone or extract the Coral directory
cd Coral

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys in .env
# GROQ_API_KEY=your_groq_api_key
# GOOGLE_API_KEY=your_gemini_api_key (optional)

# Run
python main.py
```

### Running as Background Agent

Use `Coral_Agent.vbs` to launch Coral silently without a console window:

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw main.py", 0
```

---

## Global Hotkeys

| Hotkey | Action | Description |
|--------|--------|-------------|
| `Ctrl+Shift+S` | **Capture Suite** | Opens the fullscreen overlay → snip a region → opens the annotation & tool suite |
| `Ctrl+Shift+G` | **Command Center** | Opens the fullscreen overlay → snip a region → opens the AI chat popup for natural language commands |
| `Ctrl+Shift+X` | **Screen Recorder** | Opens the fullscreen overlay → select a region → starts recording that region as MP4 |

> All hotkeys are customizable in Settings. Changes require an app restart.

---

## Interaction Modes

### 1. Capture Suite (Snip Mode)

Triggered by `Ctrl+Shift+S`. After snipping, Coral opens the **Capture Suite Popup** — a visual annotation toolbar with:

- **Copy** — Copy the snip to clipboard
- **Save** — Save the snip as PNG to the detected folder
- **OCR** — Extract text from the snip via Tesseract
- **Pin / Pin Live** — Pin a static or live-updating snippet to the screen
- **Annotate** — Draw, highlight, add text, arrows on the snip
- **QR Scan** — Decode any QR codes or barcodes in the snip
- **Color Picker** — Extract dominant colors (hex + RGB)
- **Remove BG** — AI background removal
- **Blur** — Apply Gaussian blur
- **Wallpaper** — Set the snipped image as desktop wallpaper
- **Ask AI** — Send the snip to the AI chat for analysis

### 2. Command Center (Global Mode)

Triggered by `Ctrl+Shift+G`. After snipping, Coral opens the **Chat Popup** — a conversational AI interface where you can:

- Type natural English: *"Create a folder called Projects"*
- Use slash commands: `/create_folder Projects`
- Chain operations: *"Create a folder called Backup and move all PDFs into it"*
- Undo actions: Type `undo`
- Confirm/cancel: Type `yes`/`no` when prompted

The AI understands the folder context from your snip and executes operations in that directory.

### 3. Screen Recorder

Triggered by `Ctrl+Shift+X`. Select a region, then use the floating control panel:

- **Record/Pause** — Start/pause recording
- **Stop** — Finish and save as MP4
- **Timer** — Live recording timer display
- **Drawing Tools** — Annotate while recording (pen, highlighter, shapes)

---

## Capture Suite

The Capture Suite is Coral's visual toolkit. It provides a toolbar with the following tools:

### Annotation Tools

| Tool | Icon | How It Works |
|------|------|-------------|
| **Pen** | ✏️ | Freehand drawing with configurable color and thickness. Uses QPainter on a transparent canvas overlay |
| **Highlighter** | 🖍️ | Semi-transparent stroke for highlighting regions |
| **Rectangle** | ▢ | Draw rectangles (outline or filled) |
| **Circle** | ○ | Draw ellipses/circles |
| **Arrow** | → | Draw directional arrows between two points |
| **Line** | ─ | Draw straight lines |
| **Text** | T | Click to place text with a popup input dialog |
| **Crop** | ✂️ | Drag to crop the snip to a sub-region |
| **Undo/Redo** | ↩/↪ | Step through annotation history |

### Image Processing Tools

| Tool | Tech Stack | How It Works |
|------|-----------|-------------|
| **OCR / Extract Text** | `pytesseract` → Tesseract C++ engine | Converts snip to grayscale, upscales 2x for accuracy, runs OCR, copies result to clipboard |
| **QR/Barcode Scanner** | `pyzbar` → ZBar C library | Decodes all QR codes and barcodes in the image, auto-copies data and optionally opens URLs |
| **Color Picker** | `Pillow` (quantize) | Resizes image to 100x100, quantizes to 5 colors, sorts by frequency, copies dominant hex to clipboard |
| **Background Removal** | `rembg` → U²-Net deep learning model | Runs a pre-trained neural network locally to separate foreground from background |
| **Blur** | `Pillow` (GaussianBlur) | Applies Gaussian blur with radius 10 to the entire snip |
| **Set as Wallpaper** | `ctypes` → `user32.SystemParametersInfoW` | Saves snip as BMP, calls Win32 API to set it as the desktop wallpaper |
| **Share Link** | `requests` → tmpfiles.org API | Uploads the snip as PNG to a temporary file hosting service, returns a shareable URL |

---

## Slash Commands Reference

All commands work in the **Chat Popup** (Command Center mode). You can also just describe what you want in English — the AI will figure out the action.

### File Operations

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/create_folder` | `name` | Create a new folder | `os.makedirs()` |
| `/create_file` | `name` | Create an empty file | `open()` with write mode |
| `/delete` | `name` | Delete file or folder (to Recycle Bin) | `send2trash` |
| `/copy` | `source destination` | Copy a file to destination | `shutil.copy2()` |
| `/duplicate` | `name` | Create a copy with `_copy` suffix | `shutil.copy2()` |
| `/move` | `source destination` | Move a file to a new location | `shutil.move()` |
| `/rename` | `old new` | Rename a file or folder | `os.rename()` |
| `/undo` | — | Undo the last destructive action | `UndoManager` reverse-action stack |

### Folder Operations

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/open` | `name` (optional) | Open a folder or navigate into a subfolder | `os.startfile()` |
| `/arrange` | — | Sort files into subfolders by type (Images, Documents, etc.) | `shutil.move()` by extension category |
| `/flatten` | — | Move all files from subfolders up to the current folder | `shutil.move()` recursive walk |
| `/clean` | — | Delete all empty subdirectories | `os.rmdir()` on empty dirs |
| `/shortcut` | `target` | Create a Windows `.lnk` shortcut | `win32com.client` WScript.Shell |
| `/zip` | `name` | Compress file/folder into a `.zip` archive | `zipfile.ZipFile` with deflate |
| `/unzip` | `name` | Extract a `.zip` archive | `zipfile.ZipFile.extractall()` |

### Information & Search

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/info` | `name` | Show file size, dates, type, permissions | `os.stat()` + `os.path` |
| `/usage` | — | Show disk usage breakdown by file type | `os.walk()` with size aggregation |
| `/duplicates` | — | Find duplicate files (by hash) | `hashlib.md5` file hashing |
| `/search_inside` | `query` | Search inside file contents for text matches | File content scanning with encoding detection |

### Tag System

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/tag` | `file tag` | Add a custom tag to a file | `TagManager` → `tags.json` |
| `/untag` | `file tag` | Remove a tag from a file | `TagManager` → `tags.json` |
| `/all_tags` | — | List all tagged files grouped by tag | `TagManager` scan |

> Tags are stored persistently in `tags.json`. They survive renames and are searchable system-wide.

### Image & Vision

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/extract` | — | OCR the current snip | `pytesseract` |
| `/color` | — | Extract dominant colors from snip | `Pillow` quantize |
| `/qr` | — | Scan QR/barcodes in snip | `pyzbar` |
| `/blur` | — | Apply blur to snip | `Pillow` GaussianBlur |
| `/remove_bg` | — | Remove background from snip | `rembg` (U²-Net) |
| `/wallpaper` | — | Set snip as desktop wallpaper | Win32 `SystemParametersInfoW` |
| `/link` | — | Upload snip, get shareable URL | `requests` → tmpfiles.org |
| `/pin` | — | Pin snip as always-on-top overlay | PyQt5 `QWidget` with `Qt.Tool` |
| `/pin_live` | — | Pin a **live-updating** snip | DWM Thumbnail API (`dwmapi.dll`) |

### Vault (Persistent Memory)

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/note` | `text` | Save a note to the scratchpad vault | Append to `coral_scratchpad.txt` |
| `/vault` | `n` (optional) | Read last N vault entries | File tail reading |

### System Automation

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/kill` | `app_name` | Force-close an application | `psutil.Process.terminate()` |
| `/vol` | `level` | Set system volume (0–100) | `pycaw` Windows Core Audio API |
| `/mute` | — | Toggle system mute | `pycaw` |
| `/lock` | — | Lock the workstation | `ctypes` → `user32.LockWorkStation` |
| `/sleep` | — | Put the PC to sleep | `ctypes` → `PowrProf.SetSuspendState` |
| `/timer` | `seconds` | Set a countdown timer with popup alert | `threading.Timer` + `user32.MessageBoxW` |
| `/dark_mode` | — | Toggle Windows dark mode | `winreg` registry write |
| `/empty_trash` | — | Empty the Recycle Bin | `ctypes` → `shell32.SHEmptyRecycleBinW` |
| `/sysinfo` | — | Show CPU, RAM, battery stats | `psutil` |

### Macros (Offline RPA)

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/macro_record` | `name` | Start recording mouse + keyboard events | `pynput` listeners |
| `/macro_play` | `name` | Replay a recorded macro | `pynput` controllers |

### Utilities

| Command | Arguments | What It Does | Tech |
|---------|-----------|-------------|------|
| `/convert` | `file format` | Convert image formats (PNG↔JPG↔BMP↔WebP) | `Pillow` Image.save() |
| `/bulk_rename` | `prefix` | Rename all files with a numbered prefix | `os.rename()` batch |
| `/help` | — | Show all available commands | Static HTML display |

---

## System Automation

### How Natural Language Works

When you type a plain English request like *"Create a folder called Reports and move all PDFs into it"*, the following pipeline executes:

1. **Context** is serialized: `{type: "file_explorer", path: "C:\\Users\\...", items: [...]}`
2. **Groq API** receives context + request → returns:
   ```json
   {
     "message": "I'll create a Reports folder and move all PDFs into it.",
     "action_json": [
       {"action": "create_folder", "name": "Reports", "path": "C:\\Users\\..."},
       {"action": "move_file", "from": "C:\\...\\doc1.pdf", "to": "C:\\...\\Reports\\doc1.pdf"},
       {"action": "move_file", "from": "C:\\...\\doc2.pdf", "to": "C:\\...\\Reports\\doc2.pdf"}
     ]
   }
   ```
3. **Confirmation prompt** shown to user (configurable)
4. **Executor** processes each action sequentially, pushing reverse actions to the undo stack

### Everything Search Integration

Coral integrates with **Everything** (the instant file search tool) via its native DLL:

- Uses `Everything64.dll` / `Everything32.dll` via `ctypes` C bindings
- Searches happen in microseconds across the entire filesystem
- Used for: `/search`, `find X`, app auto-discovery, and fallback resolution when files aren't in the current folder

### App Auto-Discovery

When you say *"Open this in Photoshop"*, Coral:

1. Checks registered apps in `settings.json`
2. If not found, queries Everything for `photoshop.exe`
3. Filters out installers, updaters, helpers
4. Auto-registers the discovered path for future use
5. Launches with the target file as argument

---

## Macro Recorder (Offline RPA)

### How It Works

The macro system uses `pynput` to directly interface with the OS input subsystem:

1. **Recording** (`/macro_record name`):
   - Spawns `pynput.mouse.Listener` and `pynput.keyboard.Listener` in a background thread
   - Every mouse move, click, keypress, and key release is timestamped and stored
   - Press `Esc` to stop → events saved to `macros/name.json`

2. **Playback** (`/macro_play name`):
   - Loads the JSON event array
   - Uses `pynput.mouse.Controller` and `pynput.keyboard.Controller` to replay
   - Preserves timing between events (capped at 1.5s max delay)
   - Runs in background thread so UI remains responsive

### Macro File Format

```json
[
  {"t": 0.000, "type": "move", "x": 500, "y": 300},
  {"t": 0.150, "type": "click", "x": 500, "y": 300, "btn": "Button.left", "pressed": true},
  {"t": 0.210, "type": "click", "x": 500, "y": 300, "btn": "Button.left", "pressed": false},
  {"t": 1.500, "type": "kp", "k": "h"},
  {"t": 1.560, "type": "kr", "k": "h"}
]
```

---

## Vault (Persistent Memory)

The Vault is Coral's persistent memory system:

- **Auto-capture**: Every `Ctrl+C` clipboard copy is automatically timestamped and saved to `coral_scratchpad.txt`
- **Manual notes**: `/note Remember to submit the report` appends to the vault
- **Reading**: `/vault 5` shows the last 5 vault entries
- **Auto-cleanup**: Configurable in Settings — entries older than N days are pruned on startup (default: 7 days)

---

## Living Snips

Living Snips are **real-time, hardware-accelerated screen mirrors** pinned to your desktop.

### How It Works

1. User selects a region with `/pin_live`
2. Coral creates a `PinnedSnip` widget with `Qt.Tool | Qt.WindowStaysOnTopHint`
3. Calls `DwmRegisterThumbnail()` — Windows DWM API — to create a GPU-backed live thumbnail
4. DWM streams the source window region directly to the pinned widget at **60 FPS** with zero CPU cost
5. `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` is called to exclude the pin from screen captures, preventing infinite recursion (Droste effect)

### Static Pins

Static pins (`/pin`) simply display the captured screenshot as a draggable, always-on-top image. They can be closed via right-click or `Esc`/`Delete`.

---

## Screen Recorder

### Architecture

The recorder uses a multi-widget architecture:

| Widget | Purpose |
|--------|---------|
| `RecordingBorder` | Coral-colored border drawn around the recording region |
| `RecordingCanvas` | Transparent overlay for real-time annotation during recording |
| `RecordingTopPalette` | Minimalist control bar (Record, Pause, Stop, Timer) |
| `RecordingToolPanel` | Drawing tool palette (Pen, Highlighter, Shapes, Colors) |
| `RecordingControlPanel` | Main orchestrator: manages all sub-widgets and the recording worker |

### Recording Pipeline

1. **Capture**: `PIL.ImageGrab.grab()` captures the selected region at ~30 FPS
2. **Encode**: Frames are converted to numpy arrays and written via `cv2.VideoWriter` (MP4V codec)
3. **Thread**: Recording runs in a `QThread` worker to keep UI responsive
4. **Annotation**: Drawing events on the canvas are composited onto each frame before encoding
5. **Output**: Saved as `.mp4` in the user's Videos folder, then Explorer opens with the file selected

---

## Settings & Configuration

Access via the **⚙️ gear icon** in any Chat Popup.

| Setting | Default | Description |
|---------|---------|-------------|
| Confirm before actions | ✅ On | Ask before create, move, rename operations |
| Confirm before delete | ✅ On | Extra safety for destructive operations |
| Chat Font Size | 13 | Adjustable 9–24px |
| Open QR URLs in browser | ❌ Off | Auto-launch browser on QR URL detection |
| Copy QR data to clipboard | ❌ Off | Auto-copy decoded QR data |
| Vault Auto-Cleanup | 7 days | Delete vault entries older than N days (0 = never) |
| Intelligence Provider | Groq | Switch between Groq (faster) and Gemini (native vision) |
| Capture Suite Hotkey | Ctrl+Shift+S | Customizable |
| Command Center Hotkey | Ctrl+Shift+G | Customizable |
| Screen Recorder Hotkey | Ctrl+Shift+X | Customizable |
| Confirm before macro playback | ✅ On | Ask before running a recorded macro |
| Macro notifications | ✅ On | Show status when macro starts/finishes |
| Default macro repeat count | 1 | How many times to replay a macro |

Settings are persisted in `settings.json`.

---

## File Structure

```
Coral/
├── main.py                 # Application entry point, hotkey setup, lifecycle management
├── popup.py                # ChatPopup — AI conversation interface
├── capture_suite.py        # CaptureSuitePopup — visual annotation & tool suite
├── overlay.py              # SelectionOverlay — fullscreen snip selector + PinnedSnip
├── recording.py            # Screen recorder (border, canvas, palette, control panel)
├── context.py              # OS context capture (screenshot + window detection + path)
├── executor.py             # ActionExecutor — 40+ action implementations
├── groq_client.py          # Groq LLM client (Llama 3.3 70B)
├── gemini_client.py        # Gemini LLM client (Gemini 1.5 Flash)
├── everything_api.py       # Everything SDK wrapper (ctypes DLL binding)
├── tag_manager.py          # File tagging system (tags.json persistence)
├── undo_manager.py         # Undo stack with reverse-action support
├── settings_manager.py     # Settings persistence (settings.json)
├── settings_ui.py          # Settings window UI
├── utils.py                # Constants, theme, logger, JSON parser
├── Coral_Agent.vbs         # Silent launcher (no console window)
├── requirements.txt        # Python dependencies
├── .env                    # API keys (GROQ_API_KEY, GOOGLE_API_KEY)
├── settings.json           # User preferences
├── tags.json               # File tag database
├── coral_scratchpad.txt    # Vault / persistent memory
├── Everything64.dll        # Everything search engine DLL
├── Everything32.dll        # Everything search engine DLL (32-bit)
└── macros/                 # Recorded macro JSON files
```

---

## Undo System

Coral's undo system works by pushing **reverse actions** onto a stack whenever a destructive operation succeeds:

| Original Action | Reverse Action |
|----------------|----------------|
| `create_folder` | `delete_folder` (send to trash) |
| `create_file` | `delete_file` (send to trash) |
| `delete_file` | `restore_recycle_bin` (COM Shell restore) |
| `move_file` | `move_file_back` (reverse path) |
| `rename_file` | `rename_file_back` (swap old/new paths) |
| `create_shortcut` | `delete_shortcut` (send to trash) |
| `arrange_by_type` | `arrange_back` (reverse all moves) |

Type `undo` or `/undo` in the chat to reverse the last action.

---

## AI Provider Comparison

| Feature | Groq (Llama 3.3 70B) | Gemini 1.5 Flash |
|---------|----------------------|------------------|
| Speed | ⚡ Very fast (~500ms) | 🔄 Moderate (~1.5s) |
| Vision | ❌ Text-only (OCR proxy) | ✅ Native image understanding |
| Context Window | 128K tokens | 1M tokens |
| JSON Mode | ✅ Native `response_format` | ⚠️ Prompt-based |
| Cost | Free tier available | Free tier available |
| Best For | File operations, system commands | Image analysis, visual Q&A |

When using Groq, Coral runs OCR on the snip and injects extracted text into the prompt as a vision proxy. Gemini receives the raw image bytes for native multimodal analysis.

---

*Coral — Your desktop, your rules. 🪸*
