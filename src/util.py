
import os
from appdirs import AppDirs

# --- Appdirs Setup ---
APP_NAME = "VoiceBind"
APP_AUTHOR = "zidaneho"
version = "0.0.1"
dirs = AppDirs(APP_NAME, APP_AUTHOR)
user_data_dir = dirs.user_data_dir
os.makedirs(user_data_dir, exist_ok=True)
profiles_data_dir = os.path.join(user_data_dir, "profiles")
os.makedirs(profiles_data_dir,exist_ok=True)
keybindingsJsonPath = os.path.join(user_data_dir, "keybindings.json")
settingsJsonPath = os.path.join(user_data_dir, "settings.json")
