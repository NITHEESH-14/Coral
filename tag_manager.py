import os
import json
import utils

logger = utils.setup_logger(__name__)

TAGS_FILE = os.path.join(os.path.dirname(__file__), "tags.json")


class TagManager:
    def __init__(self):
        self.tags = {}
        self._load()

    def _load(self):
        if os.path.exists(TAGS_FILE):
            try:
                with open(TAGS_FILE, 'r') as f:
                    self.tags = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load tags: {e}")
                self.tags = {}

    def _save(self):
        try:
            with open(TAGS_FILE, 'w') as f:
                json.dump(self.tags, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tags: {e}")

    def add_tag(self, filepath, tag):
        filepath = os.path.normpath(filepath)
        tag = tag.strip().lower()
        if filepath not in self.tags:
            self.tags[filepath] = []
        if tag not in self.tags[filepath]:
            self.tags[filepath].append(tag)
            self._save()
            return True
        return False

    def remove_tag(self, filepath, tag):
        filepath = os.path.normpath(filepath)
        tag = tag.strip().lower()
        if filepath in self.tags and tag in self.tags[filepath]:
            self.tags[filepath].remove(tag)
            if not self.tags[filepath]:
                del self.tags[filepath]
            self._save()
            return True
        return False

    def get_tags(self, filepath):
        filepath = os.path.normpath(filepath)
        return self.tags.get(filepath, [])

    def search_by_tag(self, tag, folder=None):
        tag = tag.strip().lower()
        results = []
        for filepath, tags in self.tags.items():
            if tag in tags:
                # If folder is specified, only return files in that folder
                if folder:
                    folder = os.path.normpath(folder)
                    if not filepath.startswith(folder):
                        continue
                if os.path.exists(filepath):
                    results.append(filepath)
        return results

    def list_all_tags(self, folder=None):
        all_tags = set()
        for filepath, tags in self.tags.items():
            if folder:
                folder = os.path.normpath(folder)
                if not filepath.startswith(folder):
                    continue
            if os.path.exists(filepath):
                all_tags.update(tags)
        return sorted(all_tags)
