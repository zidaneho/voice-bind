import os
import json
from PyQt6.QtCore import QObject, pyqtSignal
from util import profiles_data_dir, settingsJsonPath

class ProfileManager(QObject):
    """Manages loading, saving, and switching user profiles."""
    profileChanged = pyqtSignal(dict)
    profilesListChanged = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._profiles = self._find_profiles()
        self._active_profile_name = None
        self._active_profile_data = {}
        self.load_settings()

    def _find_profiles(self):
        """Scans the profiles directory for .json files."""
        profiles = []
        for filename in os.listdir(profiles_data_dir):
            if filename.endswith(".json"):
                profiles.append(os.path.splitext(filename)[0])
        if not profiles:
            self.create_profile("default")
            return ["default"]
        return profiles

    def load_settings(self):
        """Loads app settings, including the last active profile."""
        try:
            with open(settingsJsonPath, 'r') as f:
                settings = json.load(f)
                profile_name = settings.get("active_profile", "default")
                self.switch_profile(profile_name)
        except (FileNotFoundError, json.JSONDecodeError):
            self.switch_profile("default")

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
            self._active_profile_data = {}

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

        self.profileChanged.emit(self._active_profile_data)

    def get_active_profile_name(self):
        return self._active_profile_name

    def get_all_profile_names(self):
        return self._profiles

    def create_profile(self, profile_name: str):
        """Creates a new, empty profile."""
        if profile_name in self._profiles:
            print(f"Profile '{profile_name}' already exists.")
            return
        self._profiles.append(profile_name)
        self.switch_profile(profile_name) # Switch to the new profile
        self.save_keybindings({}) # Save an empty keybinding set
        self.profilesListChanged.emit(self._profiles)


    def rename_profile(self, old_name: str, new_name: str):
        """Renames a profile."""
        if old_name not in self._profiles or new_name in self._profiles:
            return

        old_path = os.path.join(profiles_data_dir, f"{old_name}.json")
        new_path = os.path.join(profiles_data_dir, f"{new_name}.json")
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            self._profiles[self._profiles.index(old_name)] = new_name
            if self._active_profile_name == old_name:
                self.switch_profile(new_name)
            self.profilesListChanged.emit(self._profiles)


    def delete_profile(self, profile_name: str):
        """Deletes a profile."""
        if profile_name not in self._profiles or profile_name == "default":
            return # Cannot delete the default profile

        self._profiles.remove(profile_name)
        profile_path = os.path.join(profiles_data_dir, f"{profile_name}.json")
        if os.path.exists(profile_path):
            os.remove(profile_path)

        if self._active_profile_name == profile_name:
            self.switch_profile("default") # Switch to default
        self.profilesListChanged.emit(self._profiles)