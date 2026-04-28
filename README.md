# 🪸 Coral: Detailed Project Report

## 1. Executive Summary
Coral is an advanced, context-aware AI desktop agent designed to seamlessly bridge the gap between user intent and system-level execution. By integrating multi-model intelligence (Google Gemini and Groq) with robust perception capabilities (OCR and UI Automation) and workflow automation (Macro Engine and Everything Search API), Coral acts as an omnipresent desktop companion. It is engineered to "see" the screen, "understand" complex language, and "execute" multi-step actions effortlessly.

![Coral Banner](https://github.com/NITHEESH-14/Coral/raw/main/Coral_Snip.png)

## 2. Core Architecture & Intelligence

### 2.1 Dual-Provider "Brain" System
Coral operates using a dynamic, multi-modal intelligence layer capable of switching providers on the fly:
- **Google Gemini Integration:** Designed for deep vision processing, UI layout analysis, and rich multimodal understanding. Supports specific brain versions like `gemini-1.5-pro` and `gemini-2.0-flash`.
- **Groq Integration:** Designed for ultra-low latency, blazing-fast text processing, and system-level decision-making utilizing Llama 3 models (e.g., `llama-3.3-70b`).
- **Dynamic Selection:** Users can hot-swap the underlying brain version from the Settings menu without restarting the core application, ensuring optimal speed-to-accuracy ratios based on the task.

### 2.2 System Perception (Vision & UIA)
Coral does not operate blind. It uses overlapping perception techniques to understand the desktop:
- **Smart Snipping:** Users can capture arbitrary screen regions (`Ctrl+Shift+S`).
- **UI Automation (UIA) Scraper:** Analyzes the active desktop window to extract structured data, buttons, and text hierarchies even when optical character recognition (OCR) might fail.
- **Context Generation:** The agent receives a JSON-structured digest of the current desktop state (active folders, highlighted files, selected text) alongside every prompt.

## 3. Features & Tools

### 3.1 The Capture Suite
When a snip is taken, Coral opens a rich image editor:
- **Annotation & Redaction:** Blur sensitive information, highlight text, or draw arrows and shapes directly onto the screen.
- **Data Alchemy Mode:** Automatically extract code blocks or CSV tables from screenshots.
- **Auto-Actions:** Built-in settings can automatically decode QR codes, extract URLs, and copy detected text to the clipboard the moment a snip is taken.

### 3.2 Automation & Macro Engine
- **Macro Recording (`Ctrl+Shift+X`):** Records sequential user actions (mouse clicks, dragging, keyboard inputs).
- **Macro Playback:** Replays recorded actions with adjustable repeat counts, useful for repetitive data entry or game automation.
- **Fail-Safes:** Includes toast notifications and confirmation dialogues before executing destructive or repetitive macros.

### 3.3 Universal Application Launcher
- **Everything API Integration:** Coral natively connects to the *Everything* search engine SDK. When asked to "open" an app, it bypasses generic file searches, identifies the correct executable in milliseconds, and launches it directly.
- **Fuzzy Matching:** Understands generic names (e.g., "open word" -> `WINWORD.exe`) and fallback routines for resilient execution.

### 3.4 Persistent Settings & Vault
- **Vault System:** A temporary, managed storage directory for snips, extracted tables, and temporary files. Includes an auto-cleanup engine that purges files older than a user-defined threshold (e.g., 7 days).
- **Auto-Save Preferences:** A responsive, glassmorphic UI where UI toggles, hotkeys, and model choices persist instantly.

---

## 4. Comprehensive Command Reference

Coral supports a massive suite of slash commands and conversational prompts.

### 📁 File Management
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/create_folder` | `[folder name]` | Creates a new directory in the current context |
| `/create_file` | `[file name]` | Creates a blank file |
| `/delete` | `[file or folder]` | Moves a file/folder to the recycle bin |
| `/copy` | `[file] to [destination]` | Copies a file to a new location |
| `/duplicate` | `[file name]` | Creates a direct copy of the file in the same folder |
| `/move` | `[file] to [destination]` | Moves a file |
| `/rename` | `[old] to [new]` | Renames a file or folder |
| `/open` | `[folder name]` | Opens a folder in Windows Explorer |
| `/shortcut` | `[target file]` | Generates a `.lnk` shortcut for the file |
| `/info` | `[file name]` | Displays deep metadata about a file |
| `/zip` | `[file or folder]` | Compresses the target into an archive |
| `/unzip` | `[file.zip]` | Extracts the archive into the current context |

### 🗃️ Organization & Tagging
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/bulk_rename` | `[prefix]` | Renames all files in context sequentially |
| `/tag` | `[file] as [tag]` | Assigns a searchable metadata tag to a file |
| `/untag` | `[file] remove [tag]` | Removes a specific tag |
| `/arrange` | *(none)* | Auto-sorts files into categorized folders |
| `/flatten` | *(none)* | Extracts all files from subdirectories into the root |
| `/clean` | *(none)* | Cleans up temporary/junk files |
| `/duplicates` | *(none)* | Finds duplicate files in the context |
| `/all_tags` | *(none)* | Lists all actively used tags |

### 🖼️ Image & Media
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/convert` | `[file] to [format]` | Converts media (e.g., `.png` to `.jpg`) |
| `/qr` | `[text / URL]` | Generates a QR code image |
| `/extract` | *(none)* | Extracts text/OCR from the context image |
| `/remove_bg` | *(none)* | Removes the background from the context image |

### ⚙️ System Controls
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/vol` | `[0–100]` | Adjusts the system master volume |
| `/timer` | `[Time] [sec/min/hr] [Msg]`| Sets a background countdown timer |
| `/kill` | `[app name]` | Force-closes a running application |
| `/mute` | *(none)* | Mutes the system volume |
| `/lock` | *(none)* | Locks the Windows session |
| `/sleep` | *(none)* | Puts the computer to sleep |
| `/empty_trash` | *(none)* | Empties the Windows Recycle Bin |
| `/wallpaper` | *(none)* | Sets the context image as the desktop wallpaper |

### 🛠️ Utilities & Automation
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/search_inside` | `[query]` | Greps/searches for text inside files in context |
| `/vault` | `[number]` | Displays recent items from the Vault |
| `/note` | `[text]` | Saves a quick note to the scratchpad |
| `/macro_record`| `[macro name]` | Begins recording mouse/keyboard events |
| `/macro_play` | `[macro name]` | Replays a saved macro |
| `/code` | `[filename]` | Triggers Data Alchemy to extract code to file |
| `/table` | `[filename]` | Triggers Data Alchemy to extract table to CSV |
| `/undo` | *(none)* | Reverts the last file operation |
| `/help` | *(none)* | Opens the command helper UI |
| `/sysinfo` | *(none)* | Displays CPU/RAM/System statistics |

---

## 5. Security & Isolation
Coral enforces strict data hygiene. The project utilizes localized `.env` variables to store API tokens (Google Gemini / Groq). The agent cannot transmit these keys, and repository push protections ensure that the project is completely open-source-safe. Operations are strictly tethered to the user's active context window unless explicitly overridden by global commands.
