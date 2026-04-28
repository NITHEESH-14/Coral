# Coral: Presentation Context

## 1. Problem Statement
The modern desktop suffers from a 'context gap'. While users see a wealth of information on their screens, traditional OS tools treat this data as static pixels, making it impossible for the system to understand or act upon visual content without tedious manual intervention.

*   **Static & Disconnected Tools:** Standard snipping utilities only capture flat pixels with zero context, forcing users to juggle separate apps for text extraction (OCR), media editing, and AI search.
*   **Lack of System Integration:** Current desktop AI assistants behave like isolated chatbots rather than deeply integrated operating system tools.
*   **High Costs & Privacy Risks:** Relying on premium cloud-based AI solutions compromises offline functionality, exposes sensitive desktop data, and requires expensive monthly subscriptions.
*   **Repetitive Workflow Bottlenecks:** Users lose significant productivity manually transferring data between generic visual tools and their actual destination (e.g., manually retyping visual tables into Excel).

## 2. Proposed Solution
**Coral** is a next-generation, agentic desktop assistant designed to bridge the gap between vision and action. By fusing a powerful screen capture suite with an LLM-driven command center, it transforms the desktop from a display of pixels into an interactive, context-aware workspace.

*   **Actionable Vision:** Turns flat screenshots into interactive, AI-ready data.
*   **Universal Slash Commands:** One-touch OS control and automated media editing.
*   **Private & Zero-Cost:** Local AI processing with no fees or data exposure.
*   **Instant RPA:** Easy macro recording to automate tasks directly from your screen.

## 3. Working
Coral operates persistently in the background and is triggered via a refined interaction model using two primary global hotkeys:
*   **`Ctrl + Shift + S` (The Capture Suite):** Focuses on screen interaction. Users select a region to trigger advanced OCR, live editing (annotating/redacting), smart type conversions (e.g., Image Table -> Excel), or generate instant expiring web links for sharing. It also enables "Vision" data extraction.
*   **`Ctrl + Shift + G` (The Command Center):** An overlay for system-level control and LLM interaction. Users can run standard conversational AI prompts or use powerful `/commands` (e.g., `/dark_mode`, `/sysinfo`, `/lock`) to automate Windows natively. 

Images are Base64-encoded and transmitted seamlessly to vision models, allowing the assistant to "see" colors, system UI, and complex layouts perfectly.

## 4. Tech Stack
*   **Core Backend:** Python 3.11+
*   **Desktop UI Framework:** `PyQt6` (for the high-performance, semi-transparent Capture Suite and HUD overlay).
*   **Image & Media Manipulation:** `Pillow` (processing), `OpenCV` (redaction/blur), `rembg` (AI-based BG removal), `ColorThief` (hex extraction), `pyzbar` (QR scanning).
*   **System Automation & Interaction:** `pyautogui` (RPA/Macros), `pycaw` (Native Audio control), `keyboard`/`pynput` (Global Hotkeys).
*   **OCR Engine:** `Tesseract OCR` with multi-mode config (Best for high-accuracy document extraction).
*   **Vision AI Infrastructure (The "Brain"):** Powered by locally hosted Large Multimodal Models (LMMs) via **Ollama**, ensuring 100% data privacy and offline functionality.
    *   **Primary Models:** `Llama 3.2-Vision` and `Moondream` for high-speed edge reasoning and image-to-text conversion.
*   **Data & Storage:** JSON-based state management and a Persistent Markdown Vault for long-term "copy-paste" memory.

## 5. Innovation Compared to Existing Tools 
*   **Smart Vision:** Understands image context to automate complex actions like filing tickets or sorting media.
*   **Dynamic Monitoring:** Tracks active screen regions (e.g., progress bars) to trigger alerts or macros automatically.
*   **Unified Control:** A single `/command` bridge for media tools, system management, and deep OS automation.
*   **Integrated RPA:** Free, local macro recording to instantly automate repetitive manual UI workflows.
*   **Offline Security:** 100% private, local AI processing with zero subscription fees or data exposure.

## 6. Applications (All)
1. Intelligent Capturing & Professional Recording: Beyond standard screenshots, Coral offers frame-aware high-fidelity Video Recording designed for tutorials and precise bug reporting. This is paired with a non-destructive live annotation suite, allowing users to draw arrows, highlight code, and redact sensitive information like passwords or faces immediately before saving or sharing.

2. Deep OS Command Center (45+ Commands): Coral provides a unified global shortcut (Ctrl+Shift+G) that grants instant control over the entire operating system without ever opening a terminal. This interface handles complex system tasks like secure volume management, multi-file zipping, process termination (/kill), and real-time hardware diagnostics (/sysinfo) through a simple, natural slash-command interface.

3. Vision-Powered Knowledge Extraction: By utilizing a multimodal LLM as the "Eyes" of the system, Coral can interpret intent from visual data. It doesn't just copy text; it understands structure—allowing it to extract raw functional code from videos, reconstruct complex image-based tables into fully editable Excel spreadsheets, and perform semantic searches through a visual "Time Machine" of your past workspace.

4. Agentic Workflows & Living Regions: This feature introduces "Interactive Regions," which allow the AI to actively monitor specific parts of your screen in real-time. Coral can "babysit" long-running background tasks like video renders or software downloads, automatically notifying the user or triggering complex RPA automation scripts the moment a progress bar hits 100% or an error message appears.

5. Creator's Creative Suite: Coral brings professional-grade media manipulation tools directly into the desktop workflow. Users can perform instant AI-powered background removal for asset creation, 4x resolution upscaling for low-quality snips, dominant hex-color extraction for design consistency (/color), and instant decoding of barcodes or QR codes without needing external software.

6. Secure Memory & Instant Sharing: Privacy is a core pillar; Coral features a 100% private Persistent Vault (Scratchpad) that logs visual context and copied data locally, ensuring your information never leaves your machine. For collaboration, it can generate temporary, expiring web links (/link) that allow you to share visual snips securely across Discord, Slack, or Email with zero friction.
