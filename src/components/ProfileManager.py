import os
import json
from PyQt6.QtCore import QObject, pyqtSignal
from util import profiles_data_dir, settingsJsonPath

class ProfileManager(QObject):
    """Manages loading, saving, and switching user profiles."""
    # Signal emitted when the active profile is changed or its data is updated.
    # The payload will be the dictionary of keybindings for the new profile.
    profileChanged = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._profiles = self._find_profiles()
        self._active_profile_name = None
        self._active_profile_data = {}
        self.load_settings() # This will load the last active profile

    def _find_profiles(self):
        """Scans the profiles directory for .json files."""
        profiles = []
        for filename in os.listdir(profiles_data_dir):
            if filename.endswith(".json"):
                profiles.append(os.path.splitext(filename)[0])
        return profiles if profiles else ["default"]

    def load_settings(self):
        """Loads app settings, including the last active profile."""
        try:
            with open(settingsJsonPath, 'r') as f:
                settings = json.load(f)
                profile_name = settings.get("active_profile", "default")
                self.switch_profile(profile_name)
        except (FileNotFoundError, json.JSONDecodeError):
            self.switch_profile("default") # Fallback to default

    def save_settings(self):
        """Saves the current active profile to settings.json."""
        settings = {"active_profile": self._active_profile_name}
        with open(settingsJsonPath, 'w') as f:
            json.dump(settings, f, indent=4)

    def switch_profile(self, profile_name: str):
        """Switches the active profile and loads its data."""
        if not profile_name:
            return
            
        self._active_profile_name = profile_name
        profile_path = os.path.join(profiles_data_dir, f"{profile_name}.json")
        try:
            with open(profile_path, 'r') as f:
                self._active_profile_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._active_profile_data = {} # Start with empty if not found/invalid
        
        print(f"Switched to profile: {profile_name}")
        self.save_settings()
        self.profileChanged.emit(self._active_profile_data)

    def get_keybindings(self):
        """Returns the keybindings for the currently active profile."""
        return self._active_profile_data.get("keybindings", {})

    def save_keybindings(self, keybindings: dict):
        """Saves the given keybindings to the active profile file."""
        if not self._active_profile_name:
            return

        self._active_profile_data["keybindings"] = keybindings
        profile_path = os.path.join(profiles_data_dir, f"{self._active_profile_name}.json")
        with open(profile_path, 'w') as f:
            json.dump(self._active_profile_data, f, indent=4)
        
        # Emit signal to notify all parts of the app that data has changed
        self.profileChanged.emit(self._active_profile_data)

    def get_active_profile_name(self):
        return self._active_profile_name

    def get_all_profile_names(self):
        return self._profiles