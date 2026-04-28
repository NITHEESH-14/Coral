import os
import json

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.config = {
                "confirm_actions": True,
                "confirm_deletes": True,
                "applications": {
                    "vs code": "code",
                    "notepad": "notepad",
                },
                "hotkey_snip": "<ctrl>+<shift>+s",
                "hotkey_global": "<ctrl>+<shift>+g",
                "hotkey_record": "<ctrl>+<shift>+x"
            }
            cls._instance.load()
        return cls._instance

    def load(self):
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception:
                pass
                
    def save(self):
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.config.get(key, default)
        
    def set(self, key, value):
        self.config[key] = value
        self.save()
    
    def get_app_command(self, app_name):
        """Look up an app name (case-insensitive) and return its command."""
        apps = self.config.get("applications", {})
        for name, cmd in apps.items():
            if name.lower() == app_name.lower():
                return cmd
        return None
    
    def get_app_names(self):
        """Return list of registered app names."""
        return list(self.config.get("applications", {}).keys())
