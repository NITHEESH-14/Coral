import os
import copy
from io import BytesIO
from dotenv import load_dotenv
import utils

logger = utils.setup_logger(__name__)

# Load .env file
load_dotenv()

SYSTEM_PROMPT = """You are Coral, an advanced, highly intelligent AI desktop assistant for Windows. You possess the capabilities of a top-tier GenAI chatbot, able to reason, converse, and help with complex tasks, while ALSO being deeply integrated into the user's operating system.

You receive two inputs:
1. A context object (may contain a folder path and items for snip mode, or type="global" for system-wide mode).
2. The user's plain English request.

YOUR BEHAVIOR:
1. CONVERSATIONAL GENAI: If the user asks a conversational question, wants to chat, or asks for general knowledge (e.g., "hi", "how are you", "write a python script", "what is 2+2"), act as a helpful AI assistant. Provide your full conversational response in the "message" field, and set "action_json" to null.
2. SYSTEM AUTOMATION: If the user explicitly asks you to perform a filesystem or system action (e.g., "create a folder", "delete this", "open Chrome"), determine the correct action and provide it in "action_json", with a short confirmation in "message".

AMBIGUITY HANDLING:
- If a request is ambiguous (e.g., "open test" when there is both a folder named "test" and a file named "test.txt" in the context), you MUST NOT guess. Instead, ask the user: "Did you mean the 'test' folder or the 'test.txt' file?" and set action_json to null.
- This also applies if X matches both an application name AND a file/folder name. Ask for clarification.

AVAILABLE ACTIONS:
- open_in_app: {"app_name": "chrome|notepad|etc", "target": ""}
- open_folder: {"path": "C:\\\\..."}
- move_file: {"path": "C:\\\\source", "name": "file.txt", "dest": "C:\\\\dest"}
- delete_file: {"path": "C:\\\\path", "name": "file.txt"}
- create_folder: {"path": "C:\\\\path", "name": "New Folder"}
- search_global: {"query": "filename", "open": false}
- search_by_tag: {"tag": "urgent"}
- add_tag: {"path": "...", "tag": "..."}

- If user asks to find/search something, use search_global with open=false. If they ask to OPEN a specific file, use search_global with open=true.
- When user says "open X": If X is clearly a document, open it. OTHERWISE, ALWAYS use open_in_app with app_name="X" and target="" (empty) to launch it. DO NOT tell the user it isn't in their context. Just use open_in_app and let the system find it.

DATA ALCHEMY MODE:
If the user asks to save a snip as code or a table, provide the CLEANEST possible extraction in the message/content. For code, ensure no markdown backticks are in the content if saving to a file. For tables, use CSV format.

CRITICAL FORMATTING RULE:
You MUST ALWAYS return a valid JSON object matching this structure:
{
  "message": "Your text response here",
  "action_json": { ... } // or null if no system action is required
}
Never output raw markdown without the JSON wrapper."""


class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = None
        self.history = []

        try:
            from google import genai
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            logger.error("Gemini dependencies missing. Run 'pip install google-genai'")
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
        
        from settings_manager import SettingsManager
        self.settings = SettingsManager()

    def _get_models(self):
        pref = self.settings.get("gemini_model", "gemini-2.0-flash")
        models = [pref]
        for m in self._VISION_MODELS:
            if m != pref:
                models.append(m)
        return models

    def reset_history(self):
        self.history = []

    def get_action(self, context_data, user_text):
        if not self.client or not self.api_key:
            return "Gemini API Key missing or library not installed. Please check your .env file.", None

        import time, re
        from google.genai import types
        has_image = "image" in context_data and context_data["image"]

        # Build a clean context without heavy fields
        safe_context = copy.deepcopy(context_data)
        safe_context.pop("image", None)
        safe_context.pop("ui_elements", None)
        safe_context.pop("window_info", None)

        # Build prompt with UIA data as supplementary context
        ui_summary = context_data.get("ui_summary", "")
        has_ui_data = context_data.get("has_ui_data", False)

        prompt_parts = [f"{SYSTEM_PROMPT}\n\nCONTEXT: {safe_context}"]

        if has_ui_data and ui_summary:
            prompt_parts.append(
                f"[STRUCTURAL UI ANALYSIS (from OS Accessibility Tree)]:\n{ui_summary}"
            )

        prompt_parts.append(f"USER REQUEST: {user_text}")
        prompt = "\n\n".join(prompt_parts)

        # Build content parts for the new SDK
        contents = [types.Part.from_text(text=prompt)]
        if has_image:
            buffered = BytesIO()
            context_data["image"].save(buffered, format="PNG")
            img_bytes = buffered.getvalue()
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))

        last_error = None
        models = self._get_models()
        for model_name in models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents
                    )
                    text = response.text.strip()

                    # Clean JSON if wrapped in markdown
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()

                    import json
                    data = json.loads(text)
                    msg = data.get("message", "Action prepared.")
                    action = data.get("action_json")

                    self.append_history("user", user_text)
                    self.append_history("assistant", text)
                    return msg, action

                except Exception as e:
                    err_str = str(e)
                    last_error = e
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        delay_match = re.search(r'retry in (\d+)', err_str, re.IGNORECASE)
                        wait_secs = int(delay_match.group(1)) if delay_match else 10
                        if attempt == 0 and wait_secs <= 3:
                            logger.warning(f"{model_name} rate-limited, waiting {wait_secs}s...")
                            time.sleep(wait_secs)
                            continue
                        else:
                            logger.warning(f"{model_name} rate-limited (wait {wait_secs}s), skipping to next model...")
                            break
                    else:
                        break

        logger.error(f"All Gemini models exhausted: {last_error}")
        return "⚠️ Gemini is temporarily rate-limited. Please try again later or switch models.", None

    # Models to try in order — if one is rate-limited, fall to the next
    _VISION_MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"]

    def describe_image(self, context_data, user_text="Describe this image in detail."):
        """
        Dedicated visual analysis using Gemini's native vision.
        Called by main.py when the user asks a visual question about their snip.
        Tries multiple models with auto-retry on rate limits.
        Returns a plain-text description (no JSON action).
        """
        if not self.client or not self.api_key:
            return "Gemini API Key missing. Cannot perform visual analysis.", None

        has_image = "image" in context_data and context_data["image"]
        if not has_image:
            return "No image available to describe. Take a snip first.", None

        import time, re
        from google.genai import types

        # Build a focused vision prompt
        prompt = (
            "You are a visual analysis assistant. Look at the attached screenshot/image "
            "and respond to the user's request. Be specific and detailed about what you see.\n\n"
            f"USER REQUEST: {user_text}"
        )

        buffered = BytesIO()
        context_data["image"].save(buffered, format="PNG")
        img_bytes = buffered.getvalue()

        contents = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
        ]

        last_error = None
        models = self._get_models()
        for model_name in models:
            for attempt in range(2):  # max 2 attempts per model (1 retry)
                try:
                    logger.info(f"Vision: trying {model_name} (attempt {attempt + 1})")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents
                    )
                    description = response.text.strip()

                    self.append_history("user", user_text)
                    self.append_history("model", description)
                    return description, None

                except Exception as e:
                    err_str = str(e)
                    last_error = e

                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        # Extract retry delay from error if present
                        delay_match = re.search(r'retry in (\d+)', err_str, re.IGNORECASE)
                        wait_secs = int(delay_match.group(1)) if delay_match else 10

                        if attempt == 0 and wait_secs <= 3:
                            logger.warning(f"{model_name} rate-limited, waiting {wait_secs}s before retry...")
                            time.sleep(wait_secs)
                            continue
                        else:
                            logger.warning(f"{model_name} rate-limited (wait {wait_secs}s), skipping next model...")
                            break  # move to next model
                    else:
                        logger.error(f"Gemini vision error ({model_name}): {e}")
                        break  # non-rate-limit error, try next model

        # All models failed
        logger.error(f"All Gemini vision models exhausted. Last error: {last_error}")
        return (
            "⚠️ Gemini vision is temporarily rate-limited. "
            "Please try again later or ask a non-visual question."
        ), None

    def append_history(self, role, content):
        """Standardized interface to add messages to memory (maps assistant to model)."""
        r = "model" if role == "assistant" else role
        self.history.append({"role": r, "parts": [content]})
