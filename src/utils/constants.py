"""Application-wide constants. Never scatter these values around the codebase."""
from pathlib import Path

APP_NAME = "Anime Expeditions Auto Fishing"
APP_DISPLAY_NAME = "anime expeditions\nauto fishing"
APP_VERSION = "1.0.0"
APP_AUTHOR = "y3levi"

# resolved runtime paths
CONFIG_FILE_NAME = "config.json"
PROFILES_DIR_NAME = Path("src") / "config" / "profiles"
LOG_DIR_NAME = Path("logs")
DEFAULT_PROFILE_NAME = "default"

# default hotkeys
DEFAULT_HOTKEY_TOGGLE = "f6"
DEFAULT_HOTKEY_EMERGENCY = "f7"

# threading
ENGINE_THREAD_NAME = "FishingEngineThread"
DEBUG_THREAD_NAME = "DebugWindowThread"

# timing
MIN_LOOP_SLEEP_S = 0.005
HOTKEY_DEBOUNCE_S = 0.3
