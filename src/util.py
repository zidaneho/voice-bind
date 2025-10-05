
import os
from appdirs import AppDirs

# --- Appdirs Setup ---
APP_NAME = "VoiceBind"
APP_AUTHOR = "zidaneho"
dirs = AppDirs(APP_NAME, APP_AUTHOR)
user_data_dir = dirs.user_data_dir
os.makedirs(user_data_dir, exist_ok=True)
keybindingsJsonPath = os.path.join(user_data_dir, "keybindings.json")
