"""Calibration manager — handles region persistence."""
from typing import Optional, TYPE_CHECKING
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.config.config_manager import ConfigManager

logger = get_logger("calibration")


class CalibrationManager:
    """Manages the calibrated screen region for fishing bar capture."""

    def __init__(self, config_manager: "ConfigManager") -> None:
        self._cfg = config_manager

    def get_region(self) -> Optional[dict]:
        """Return calibrated region or None."""
        return self._cfg.get_region()

    def save_region(self, region: dict) -> None:
        """
        Persist region to config.
        region must have keys: x, y, width, height (all int).
        """
        validated = {
            "x": int(region["x"]),
            "y": int(region["y"]),
            "width": int(region["width"]),
            "height": int(region["height"]),
        }
        self._cfg.set_region(validated)
        logger.info(f"Calibration saved: {validated}")

    def clear_region(self) -> None:
        """Remove calibration."""
        self._cfg.set_region(None)
        logger.info("Calibration cleared")

    def is_calibrated(self) -> bool:
        return self.get_region() is not None

    def get_water_position(self) -> Optional[dict]:
        return self._cfg.get("capture", "water_click_position")

    def save_water_position(self, pos: dict) -> None:
        validated = {"x": int(pos["x"]), "y": int(pos["y"])}
        self._cfg.set("capture", "water_click_position", value=validated)
        self._cfg.save()
        logger.info(f"water position: {validated}")

    def clear_water_position(self) -> None:
        self._cfg.set("capture", "water_click_position", value=None)
        self._cfg.save()

    def has_water_position(self) -> bool:
        return self.get_water_position() is not None
