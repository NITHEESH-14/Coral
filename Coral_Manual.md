# Coral: The Agentic Desktop Assistant Manual

Coral is always reachable via these system-wide hotkeys:

- **`Ctrl + Shift + S` (The Capture Suite):**
  - **Primary Function:** Focused on screen interaction and "Vision" data.
  - **Action:** Triggers the selection overlay to capture a specific region of your screen. 
  - **The 16 Pro Tools:** 
    1.  **Pen (Draw):** Freehand drawing with adjustable size and colors.
    2.  **Arrow:** Draw perfect pointers to highlight areas.
    3.  **Line:** Draw straight lines exactly where needed.
    4.  **Rectangle:** Box in important sections.
    5.  **Circle:** Encircle key details.
    6.  **Highlighter:** Semi-transparent marking for text.
    7.  **Number Bullets:** Iterative steps (1, 2, 3...) that auto-increment.
    8.  **Callout:** Add speech bubbles and thought clouds with text.
    9.  **Text Tool:** Place standard text labels anywhere.
    10. **Blur:** Anonymize and redact sensitive information instantly.
    11. **BG Removal:** One-click background strip (transparency export).
    12. **OCR (Extract):** Extract English text directly from the image.
    13. **QR/Barcode:** Scan and open links from QR codes or barcodes.
    14. **Color Picker:** Extract Hex/RGB codes from the image context.
    15. **Pin (Always-on-Top):** Keep your capture floating above all apps.
    16. **Save:** Quickly export your final annotated masterpiece.

- **`Ctrl + Shift + X` (The Screen Recorder):**
  - **Primary Function:** Professional-grade video capture of screen activities.
  - **Action:** Captures active video and audio with a live annotation HUD.
  - **The 10 Performance Tools:**
    1.  **Pen:** Draw freehand logic or sketches during live recording.
    2.  **Arrow:** Point to UI elements while explaining features.
    3.  **Line:** Underline or separate content areas in real-time.
    4.  **Rectangle:** Frame active windows or buttons.
    5.  **Circle:** Draw focus to specific interactive zones.
    6.  **Highlighter:** Emphasize text or data points during a presentation.
    7.  **Mosaic Blur:** Instantly scrub out sensitive data while the video is rolling.
    8.  **Pointer Tool:** Toggle between drawing mode and standard UI interaction.
    9.  **Duration Timer:** Visible real-time tracker of your recording length.
    10. **Export Engine:** Automatic MP4 conversion and save to the Recordings folder.

- **`Ctrl + Shift + G` (The Command Center):**
  - **Primary Function:** Focused on system-level control and "Brain" configuration.
  - **Action:** Opens the Coral Chat Popup in **Global Mode**, giving you full OS-level control.

---

## 🛠️ Intelligence Providers
Toggle Coral's brain in the **Settings (⚙️)**:
*   **Groq (Llama 3.3):** Sub-second response speed. Best for system control and logic.
*   **Google Gemini (1.5 Flash):** Multimodal Vision. Best for "Ask AI" about visual context.

---

## ⌨️ Full Slash Command Reference

### 🧪 Data Alchemy
- **/code [filename]**: Transmute snip into a clean, sanitized code file.
- **/table [filename]**: Transmute visual tables into structured CSV data.

### 📂 File Management
- **/create_folder [name]**: Creates a new folder in the active path.
- **/create_file [name]**: Creates a new empty text file.
- **/delete [name]**: Sends the specified file or folder to the Recycle Bin.
- **/copy [source] [dest]**: Copies a file or folder to a new location.
- **/move [source] [dest]**: Moves a file/folder and updates context.
- **/rename [old] [new]**: Changes the name of the specified local item.
- **/duplicate [name]**: Creates an instant "copy" of a file in the same folder.
- **/open [folder]**: Navigates into a folder for AI context processing.

### 📦 Archives & Organization
- **/zip [name]**: Compresses files/folders into a .zip archive.
- **/unzip [file]**: Extracts everything from a zip archive.
- **/arrange**: Sorts all local files into clean category folders.
- **/flatten**: Moves all subfolder files to the top level.
- **/clean**: Deletes all empty folders in the current directory.
- **/shortcut [target]**: Creates a native Windows shortcut (.lnk).

### 🏷️ Tagging System
- **/tag [file] [tag]**: Adds a searchable metadata tag to a file.
- **/untag [file] [tag]**: Removes a specific tag from a file.
- **/all_tags**: Opens the Tag Collection browser.

### 👁️ Image & Vision
- **/extract**: Perform high-fidelity OCR on the active snip.
- **/color**: Extract Hex and RGB codes from the snip pixels.
- **/qr**: Scan and interpret QR codes or barcodes.
- **/remove_bg**: Remove background from any snipped object.
- **/blur**: Redact the active snip for privacy.
- **/wallpaper**: Set current snip as your Desktop Wallpaper.
- **/pin**: Pin the current capture as a floating window.

### ⚙️ System & Power
- **/sysinfo**: Display live CPU, RAM, and Battery diagnostics.
- **/vol [0-100]**: Set system master volume.
- **/mute**: Mute all system audio.
- **/timer [time] [msg]**: Set a countdown with a popup alert.
- **/dark_mode**: Toggle between Light and Dark Windows themes.
- **/lock**: Instantly lock the Windows workstation.
- **/sleep**: Put the system into low-power sleep mode.
- **/empty_trash**: Securely empty the Windows Recycle Bin.
- **/kill [app]**: Force-terminate a running process by name.

### 📋 Automation & RPA
- **/macro_record [name]**: Record mouse and keys for automation.
- **/macro_play [name]**: Replay recorded actions at native speed.
- **/undo**: Reverses the last destructive file system action.
- **/note [text]**: Save a text block to the persistent vault.
- **/vault [n]**: View the last N entries in your memory vault.
- **/help**: Shows the quick-reference command menu.
- **/global**: Switches to system-wide mode.
