from typing import Optional
import numpy as np
import mss
import mss.tools
from src.utils.logger import get_logger

logger = get_logger("screen_capture")


class ScreenCapture:
    """Captures a screen region using MSS for minimal overhead."""

    def __init__(self, monitor: int = 1) -> None:
        self._monitor_index = monitor
        self._region: Optional[dict] = None
        self._mss: Optional[mss.base.MSSBase] = None
        self._mss_region: Optional[dict] = None
        self._open()

    def _open(self) -> None:
        if self._mss is None:
            self._mss = mss.mss()
            logger.debug("MSS instance opened")

    def set_region(self, region: Optional[dict]) -> None:
        """Set capture region. region dict: {x, y, width, height}."""
        self._region = region
        if region:
            self._mss_region = {
                "left": int(region["x"]),
                "top": int(region["y"]),
                "width": int(region["width"]),
                "height": int(region["height"]),
            }
        else:
            self._mss_region = None

    def set_monitor(self, monitor: int) -> None:
        self._monitor_index = monitor

    def capture(self) -> Optional[np.ndarray]:
        """Capture and return BGR numpy array. Returns None on failure."""
        if not self._mss:
            return None
        try:
            if self._mss_region:
                sct_img = self._mss.grab(self._mss_region)
            else:
                sct_img = self._mss.grab(self._mss.monitors[self._monitor_index])
            
            img = np.array(sct_img, dtype=np.uint8)
            if img.shape[2] == 4:
                return img[:, :, :3]
            return img
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            return None

    def release(self) -> None:
        """Release MSS resources."""
        if self._mss:
            self._mss.close()
            self._mss = None
            logger.debug("MSS instance closed")

    @property
    def has_region(self) -> bool:
        return self._region is not None

    @property
    def region(self) -> Optional[dict]:
        return self._region
