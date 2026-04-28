# Coral: Extended Features Blueprint

### 1. 🛠️ Local Image & Media Tools (Using Free Python Libraries)
* **`/color` (Color Picker):** Extract dominant hex codes/RGB values from the snip and copy them to the clipboard (using `Pillow` or `ColorThief`).
* **`/qr` (QR/Barcode Scanner):** Look for QR codes or barcodes in the snip and automatically open the URL or copy the text (using `pyzbar`).
* **`/remove_bg`:** Instantly strip the background out of a snipped object and save it as a transparent PNG (using `rembg`).
* **`/redact` or `/blur`:** Easily blur sensitive info (emails, passwords, faces) out of a snip before saving/sharing (using `OpenCV`).
* **`/pin`:** Pin the snipped image to the top of the screen to use as an "always-on-top" reference while working.

### 2. 👁️ Vision-Enhanced Context (The "Eyes")
* **Concept:** Use a multimodal LLM to "see" apps and websites when they are not recognized by the standard Windows metadata layer.
* **Use Case:** Snip a Spotify playlist and say *"Add these songs to my Workout folder"* or snip a bug report and say *"File this in my Trello."*

### 3. 📝 OCR & Semantic Intelligence
* **`/extract`:** Copy all text from the snip to the clipboard instantly.

### 4. 🎨 Creative Media Suite
* **`/upscale`:** Use AI to 4x the resolution of the snip.
* **`/annotate`:** Open a quick drawing overlay to add arrows/circles before saving.
* **`/wallpaper`:** Instantly set the snipped region as the desktop background.

### 5. ⚙️ System Automation
* **`/dark_mode`:** Toggle Windows Light/Dark mode.
* **`/timer [time]`:** Set a system timer.
* **`/kill [app]`:** Force close an app visible in the snip.
* **`/vol [0-100]` / `/mute`:** Control the system volume directly via the free `pycaw` library.
* **`/lock` or `/sleep`:** Instantly lock the workstation or put the PC to sleep.
* **`/empty_trash`:** Securely empty the Windows recycle bin.
* **`/sysinfo`:** Display a quick overlay of current CPU load, RAM usage, and other system parameters.
* **`/zip` / `/unzip`:** Instantly compress or decompress a selected folder or file using local Python zip libraries.
* **`/macro_record` & `/macro_play` (Offline Macros):** Record a sequence of mouse clicks and keyboard presses (via `pyautogui`) and save them locally. You can play this macro back at any time to automate repetitive offline data entry or UI clicks, essentially creating free RPA (Robotic Process Automation) scripts.
    * **Recording Termination Methods:**
        1. **Global Hotkey:** Hit `Esc` or a custom combo to stop and save instantly.
        2. **Floating Utility Button:** A tiny Always-on-Top "Stop" button in the corner.
        3. **Idle Timeout:** Automatically stops recording after X seconds of inactivity.
    * **Note:** All termination methods and hotkeys can be customized or toggled in the Coral Settings menu.

### 6. 📋 Core Productivity (Persistent Memory)
* **Persistent Offline Vault:** Whatever text you copy is automatically logged into a default local text file (`coral_scratchpad.txt`). This acts as a frictionless memory vault that survives PC reboots, allowing you to ask Coral for text you copied days ago.
* **Auto-Cleanup Feature:** A configurable setting to automatically clean up and delete entries from the text file based on a specific duration (e.g., auto-delete texts older than 7 days) to preserve long-term storage and privacy.

### 7. 🧬 The Living Snip (Interactive Regions)
* **Progress-Bar Tracking:** Monitor a specific screen region (e.g., a download or render bar). Coral will automatically notify you or play a sound when the progress hits 100% or changes state.
* **Auto-Action Trigger:** Set Coral to watch a region for specific text (e.g., "Error" or "Done"). When that text appears, it can automatically trigger a macro or run a specific `/command`.
* **Live Pinning (Dynamic Refresh):** Pin a snip to stays on top of other windows. Coral will periodically refresh the content of that specific screen coordinate, allowing you to monitor "live" data (like stock sticks, weather, or system stats) without having the full app open.

### 8. 🤖 Free Vision AI Infrastructure (The "Brain")
Coral can use 100% free Vision models for zero cost. No credit card or monthly subscriptions are needed.
* **OpenRouter (:free models):** Access world-class models (`Qwen-VL`, `Gemma-3`, `Llama-3`) via the `:free` endpoint. Best for overall stability and reasoning.
* **Groq (Llama-Vision-Preview):** Extreme speed (sub-second responses) for real-time OCR and scene understanding.
* **Ollama (Local Vision):** Run models like `Llama 3.2-Vision` or `Moondream` directly on your PC. 100% private, 100% offline, and works without an internet connection.
* **Implementation:** Images are sent via **Base64 encoding**, allowing the LLM to "see" colors, layouts, and complex UI elements perfectly.

### 9. 🚀 Elite Productivity & Aesthetics
* **`/link` (Smart Sharing):** Instantly generate a temporary, expiring web link for a snip to share via Discord, Slack, or Email without saving locally.
* **Contextual Time Machine:** Automatically tags snips with metadata (Active App, Window Title, Timestamp). Search your history for: *"The code snip I took in VS Code yesterday."*
* **Dynamic Content Adaptation:** Turn a snip into a different format instantly (e.g., Code image -> Raw Text, Table image -> Excel file, Text image -> Audio speech).
* **Aesthetic Dynamic Theming:** The Coral UI automatically color-shifts its "Organic" theme (moss green, warm tan, etc.) to match the dominant colors of your current Desktop Wallpaper.

### ⌨️ Refined Interaction Model
To keep the workflow clean, Coral uses two distinct global hotkeys:

1. **`Ctrl + Shift + S` (The Capture Suite):** 
    * **Primary Function:** Focused on screen interaction and "Vision" data.
    * **Features:**
        * **Screen Tracking:** Link images to live screen regions.
        * **Advanced OCR:** Extract text and system data.
        * **Direct Sharing:** Instantly generate `/link` for standard snips.
        * **Live Editing:** Quick-annotate tool (arrows, circles, redaction).
        * **Type Conversion:** Convert snips into different data formats (e.g., Table -> Excel, Code -> Text).

2. **`Ctrl + Shift + G` (The Command Center):**
    * **Primary Function:** Focused on system-level control and "Brain" configuration.
    * **Features:**
        * **System Automation:** Control volume, dark mode, and power states.
        * **Macro Suite:** Record, manage, and play system-level/offline macros.
        * **Diagnostics:** View live `/sysinfo` (CPU, RAM, Battery).
        * **Settings Hub:** Manage API keys, auto-cleanup durations, and theme styling.
