import os
import copy
import base64
from io import BytesIO
from dotenv import load_dotenv
from groq import Groq
import utils

logger = utils.setup_logger(__name__)

# Load .env file
load_dotenv()

SYSTEM_PROMPT_TEMPLATE = """You are Coral, an advanced, highly intelligent AI desktop assistant for Windows. You possess the capabilities of a top-tier GenAI chatbot, able to reason, converse, and help with complex tasks, while ALSO being deeply integrated into the user's operating system.

You receive two inputs:
1. A context object (may contain a folder path and items for snip mode, or type="global" for system-wide mode).
2. The user's plain English request.

YOUR BEHAVIOR:
1. CONVERSATIONAL GENAI: If the user asks a conversational question, wants to chat, or asks for general knowledge (e.g., "hi", "how are you", "write a python script", "what is 2+2"), act as a helpful AI assistant. Provide your full conversational response in the "message" field, and set "action_json" to null.
2. SYSTEM AUTOMATION: If the user explicitly asks you to perform a filesystem or system action (e.g., "create a folder", "delete this", "open Chrome"), determine the correct action and provide it in "action_json", with a short confirmation in "message".

AMBIGUITY HANDLING:
- If a request is ambiguous (e.g., "open test" when there is both a folder named "test" and a file named "test.txt" in the context), you MUST NOT guess. Instead, ask the user: "Did you mean the 'test' folder or the 'test.txt' file?" and set action_json to null.
- This also applies if X matches both an application name AND a file/folder name. Ask for clarification.

If context type is "global": You operate system-wide. Use search_global to find files/folders anywhere. Use open_in_app to launch apps. There is no specific folder restriction.
If context has a path: You operate within that folder. All file operations use that path. User can change location via commands like "go to X" or "open folder X".

You must ALWAYS reply with valid JSON format. To execute one action, return a single dictionary. To execute a macro (multiple actions in a sequence), return a JSON list of dictionaries.

Example 1 (Chat/Question):
{{
  "message": "Hello! I am Coral, your AI desktop assistant. How can I help you today?",
  "action_json": null
}}

Example 2 (Single Action):
{{
  "message": "I will create a folder called Projects.",
  "action_json": {{ "action": "create_folder", "name": "Projects", "path": "C:/Users/User/" }}
}}

Example 3 (Macro Sequence):
{{
  "message": "I will create the folder and open it in VS Code.",
  "action_json": [
    {{ "action": "create_folder", "name": "Projects", "path": "C:/Users/User/" }},
    {{ "action": "open_in_app", "app_name": "vs code", "target": "Projects", "path": "C:/Users/User/" }}
  ]
}}

Available actions and their required fields:
create_folder    -> name, path
create_file      -> name, path
delete_folder    -> name, path
delete_file      -> name, path
move_file        -> from, to
rename_file      -> old_path, new_path
create_shortcut  -> target, location, shortcut_name
arrange_by_type  -> path
open_folder      -> name (optional), path
convert_file     -> file_name, target_extension, path
copy_file        -> name, path, destination
duplicate_file   -> name, path
file_info        -> name, path
clean_empty      -> path
flatten_folder   -> path
bulk_rename      -> path, prefix (optional), suffix (optional), numbering (bool, optional), filter (ext like ".txt", optional)
find_duplicates  -> path
disk_usage       -> path
zip_files        -> name, path
unzip_files      -> name, path
add_tag          -> name, path, tag
remove_tag       -> name, path, tag
search_by_tag    -> tag, path (optional, to limit search to a folder)
list_tags        -> path (optional, to limit to a folder)
open_in_app      -> app_name, target (file/folder name or empty if just launching), path
search_global    -> query (search term), open (true to open first result, false to just list results)
color_picker     -> image (automatically handled)
qr_scanner       -> image (automatically handled)
blur_snip        -> image (automatically handled)
remove_bg        -> image (automatically handled)
set_volume       -> level (0-100), mute (bool)
system_power     -> mode ("lock", "sleep", "hibernate")
set_timer        -> seconds, label
empty_trash      -> (no args)
scratchpad       -> text

Registered applications: {apps}
When user says "open X in Y", use open_in_app with app_name matching one of the registered app names above.

When user says "open X":
If X is clearly a specific document in the context (like "report.pdf"), use open_folder or appropriate file action.
OTHERWISE, ALWAYS assume X is an application and use open_in_app with app_name="X" and target="" (empty). DO NOT restrict this to the current context path, and DO NOT tell the user it isn't in their context. Just use open_in_app and let the system find it. Do NOT use search_global for opening applications.

Rules:
- Always confirm before executing. Never say you have done it.
- Always use the path from the context object, never invent paths.
- If the request is unclear, ask for clarification in the message field.
- Set action_json to null if no action is needed (e.g. just a question).
- Never return anything outside the JSON structure.
- IMPORTANT: "open everything" means launch the Everything search application, NOT open every file. Only open all files if user explicitly says "open ALL files" or "open every file".
- Keep messages short and direct.
- If user asks to find/search something, use search_global to search the system. Set open=false. If they ask to OPEN a specific file that is not an app, use search_global with open=true. For applications, use open_in_app.
- "search using everything" or "find X using everything" means use the search_global action to search via Everything API. Do NOT launch the Everything app for search requests.
- DATA ALCHEMY MODE: If asked to save a snip as code or a table, provide the CLEANEST possible extraction in the message or content. For code, ensure no markdown backticks are in the content if saving to a file. For tables, use CSV format.
"""

# Keywords that indicate the user wants visual/image analysis (not just file ops)
_VISUAL_KEYWORDS = [
    "describe", "what is this", "what's this", "what do you see",
    "what is in", "what's in", "analyze", "read this", "look at",
    "what does", "explain this", "identify", "recogni",
    "screenshot", "image", "picture", "photo", "visual",
    "what colour", "what color", "how many", "count",
    "what text", "what app", "which app",
]

def is_visual_query(user_message: str) -> bool:
    """Return True if the user's message is asking about visual/image content."""
    msg = user_message.lower().strip()
    return any(kw in msg for kw in _VISUAL_KEYWORDS)


class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment.")
        
        # Initialize Groq client
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
        # Keep track of history for multi-turn
        self.history = []
        
    def reset_history(self):
        self.history = []

    def _pil_to_base64(self, pil_img):
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def get_action(self, context_data: dict, user_message: str) -> tuple:
        """
        Calls Groq API to get the action.
        Returns (message_str, action_dict)
        """
        # Build dynamic system prompt with registered apps
        from settings_manager import SettingsManager
        settings = SettingsManager()
        app_names = settings.get_app_names()
        apps_str = ", ".join(app_names) if app_names else "none (user can add in Settings)"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(apps=apps_str)
            
        system_msg = {
            "role": "system",
            "content": system_prompt
        }
        
        # Exclude 'image' and heavy UIA element list from raw context string
        safe_context = copy.deepcopy(context_data)
        has_image = "image" in safe_context and safe_context["image"] is not None
        if "image" in safe_context:
            del safe_context["image"]
        # Remove bulky fields that are already summarised via ui_summary
        safe_context.pop("ui_elements", None)
        safe_context.pop("window_info", None)
            
        full_user_content = f"CONTEXT:\n{safe_context}\n\nUSER REQUEST:\n{user_message}"
        
        model_to_use = settings.get("groq_model", self.model)
        user_msg_content = full_user_content
        
        # ── Additive perception: UIA + OCR when needed ─────────────────────
        # UIA structural data is always included if available.
        # OCR is added alongside when the UIA tree is sparse or absent.
        ui_summary = context_data.get("ui_summary", "")
        has_ui_data = context_data.get("has_ui_data", False)

        perception_parts = []

        # Always include structural data if available
        if has_ui_data and ui_summary:
            perception_parts.append(
                f"[STRUCTURAL UI ANALYSIS (from OS Accessibility Tree)]:\n{ui_summary}"
            )
            logger.info("Including UIA structural data in prompt")

        # Include OCR text when image exists (always alongside UIA, not replacing)
        if has_image:
            visual_text = ""
            try:
                import pytesseract
                for tess_path in [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                ]:
                    if os.path.exists(tess_path):
                        pytesseract.pytesseract.tesseract_cmd = tess_path
                        break
                img = context_data["image"].convert("L")
                w, h = img.size
                img = img.resize((w*2, h*2), 3)  # Lanczos
                visual_text = pytesseract.image_to_string(img).strip()
            except Exception as e:
                logger.warning(f"Vision proxy OCR failed: {e}")

            if visual_text:
                perception_parts.append(
                    f"[VISUAL TEXT (OCR extracted from snip)]:\n\"{visual_text}\""
                )
                logger.info("Including OCR text in prompt")

        if perception_parts:
            user_msg_content = full_user_content + "\n\n" + "\n\n".join(perception_parts)


        messages = [system_msg] + self.history + [{"role": "user", "content": user_msg_content}]
        
        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            reply_content = response.choices[0].message.content
            logger.debug(f"Groq response: {reply_content}")
            
            # Save to history for multi-turn conversations
            self.append_history("user", user_message) 
            self.append_history("assistant", reply_content)
            
            msg, action_json = utils.parse_groq_json(reply_content)
            return msg, action_json
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"Error communicating with AI: {str(e)}", {}

    def reset_history(self):
        self.history = []

    def append_history(self, role, content):
        """Standardized interface to add messages to memory."""
        self.history.append({"role": role, "content": content})
