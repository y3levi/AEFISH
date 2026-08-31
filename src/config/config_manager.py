"""Configuration manager."""
import json
import logging
import threading
import copy
from pathlib import Path
from typing import Optional, Any

from src.config.defaults import DEFAULT_CONFIG
from src.utils.logger import get_logger

logger = get_logger("config_manager")

class ConfigManager:
    def __init__(self, config_path: str | Path) -> None:
        self._lock = threading.Lock()
        self._config_path = Path(config_path)
        self._config: dict = {}
        self._profile: dict = {}
        
        self._load()
        
    def _load(self) -> None:
        with self._lock:
            if not self._config_path.exists():
                logger.info(f"Config file not found. Creating default at {self._config_path}")
                self._config = copy.deepcopy(DEFAULT_CONFIG)
                self._save_unlocked()
            else:
                try:
                    with open(self._config_path, "r", encoding="utf-8") as f:
                        user_config = json.load(f)
                    self._config = self._deep_merge(copy.deepcopy(DEFAULT_CONFIG), user_config)
                    self._migrate_unlocked()
                    logger.info("Config loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load config: {e}. Using defaults.")
                    self._config = copy.deepcopy(DEFAULT_CONFIG)
            
            profile_name = self._config.get("detection", {}).get("profile", "default")
            self._profile = self._load_profile_unlocked(profile_name)

    def _migrate_unlocked(self) -> None:
        dirty = False
        if "control" in self._config:
            control = self._config.pop("control")
            if isinstance(control, dict):
                if "prediction" in control:
                    self._config.setdefault("controller", {})["prediction"] = control["prediction"]
                if "smoothing" in control:
                    self._config.setdefault("controller", {})["smoothing"] = control["smoothing"]
                if "deadzone" in control:
                    self._config.setdefault("detection", {})["deadzone"] = control["deadzone"]
            dirty = True
        if "fishing" in self._config:
            fishing = self._config.pop("fishing")
            if isinstance(fishing, dict):
                if "recast_timeout_ms" in fishing:
                    self._config.setdefault("capture", {})["recast_timeout_s"] = float(fishing["recast_timeout_ms"]) / 1000.0
            dirty = True
        if dirty:
            logger.info("Migrated old config values to new format")
            self._save_unlocked()

    def _deep_merge(self, base: dict, override: dict) -> dict:
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = copy.deepcopy(v)
        return base

    def get(self, *keys: str, default: Any = None) -> Any:
        with self._lock:
            val = self._config
            for k in keys:
                if isinstance(val, dict) and k in val:
                    val = val[k]
                else:
                    return default
            return copy.deepcopy(val)

    def set(self, *keys: str, value: Any) -> None:
        with self._lock:
            if not keys:
                return
            d = self._config
            for k in keys[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = value
            logger.debug(f"Config set: {keys} = {value}")

    def save(self) -> None:
        with self._lock:
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            logger.info("Config saved.")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def reload(self) -> None:
        self._load()

    def get_region(self) -> Optional[dict]:
        return self.get("capture", "region")

    def set_region(self, region: Optional[dict]) -> None:
        self.set("capture", "region", value=region)
        self.save()

    def get_profile(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._profile)

    def load_profile(self, name: str) -> dict:
        with self._lock:
            self._profile = self._load_profile_unlocked(name)
            return copy.deepcopy(self._profile)

    def _resolve_profiles_dir(self) -> Path:
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return Path(getattr(sys, '_MEIPASS')) / "src" / "config" / "profiles"
        return Path(__file__).parent / "profiles"

    def _load_profile_unlocked(self, name: str) -> dict:
        prof_dir = self._resolve_profiles_dir()
        prof_path = prof_dir / f"{name}.json"
        
        if not prof_path.exists():
            logger.warning(f"Profile '{name}' not found. Falling back to default.")
            prof_path = prof_dir / "default.json"
            
        try:
            with open(prof_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load profile from {prof_path}: {e}")
            return {}
