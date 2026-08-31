import threading
from typing import Optional
from pynput.mouse import Button, Controller as PynputMouse
from src.core.controller import Action
from src.utils.logger import get_logger

logger = get_logger("mouse_controller")


class MouseController:
    """Thread-safe mouse state wrapper."""

    def __init__(self) -> None:
        self._mouse = PynputMouse()
        self._mouse_down = False
        self._lock = threading.Lock()

    def apply(self, action: Action) -> None:
        """Apply an abstract action to the mouse."""
        if action == Action.HOLD:
            self._press()
        elif action == Action.RELEASE:
            self._release()

    def _press(self) -> None:
        with self._lock:
            if not self._mouse_down:
                self._mouse.press(Button.left)
                self._mouse_down = True
                logger.debug("Mouse: PRESS")

    def _release(self) -> None:
        with self._lock:
            if self._mouse_down:
                self._mouse.release(Button.left)
                self._mouse_down = False
                logger.debug("Mouse: RELEASE")

    def emergency_release(self) -> None:
        """Unconditionally release mouse. Safe to call multiple times."""
        with self._lock:
            try:
                self._mouse.release(Button.left)
            except Exception as e:
                logger.error(f"Emergency release error: {e}")
            finally:
                self._mouse_down = False
        logger.warning("Mouse: EMERGENCY RELEASE")

    @property
    def is_pressed(self) -> bool:
        with self._lock:
            return self._mouse_down

    def reset(self) -> None:
        """Release and reset state."""
        self.emergency_release()
