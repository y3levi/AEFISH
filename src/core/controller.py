from enum import Enum
from typing import Optional, List, Tuple
import time
from src.utils.logger import get_logger

logger = get_logger("controller")


class Action(Enum):
    HOLD = "HOLD"
    RELEASE = "RELEASE"
    WAIT = "WAIT"


class Controller:
    """
    Decision controller — converts detection results into actions.
    Keeps a position history for velocity estimation and prediction.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._profile_ctrl = {}
        self._history: List[Tuple[int, float]] = []
        self._max_history: int = 8
        self._last_action = Action.WAIT
        self._velocity: float = 0.0
        self._update_params()

    def _update_params(self) -> None:
        """Read parameters from config and profile_ctrl."""
        # deadzone override
        det_cfg = self._config.get("detection", {})
        self._deadzone = det_cfg.get("deadzone", 10)
        self._prediction_enabled = self._config.get("controller", {}).get("prediction", True)
        self._history_size = self._profile_ctrl.get("history_size", 8)
        self._lookahead_ms = self._profile_ctrl.get("prediction_lookahead_ms", 50)
        self._smoothing = self._config.get("controller", {}).get("smoothing", 0.5)
        # safety margin
        self._edge_margin = self._config.get("controller", {}).get("edge_margin", 15)

    def update_config(self, config: dict, profile_ctrl: dict = None) -> None:
        """Hot-reload config and/or profile controller section."""
        self._config = config
        if profile_ctrl is not None:
            self._profile_ctrl = profile_ctrl
        self._update_params()

    def update(self,
               fish_x: Optional[int],
               zone_left: Optional[int],
               zone_right: Optional[int],
               timestamp: float) -> Action:
        """
        Compute next action given current detection snapshot.
        Returns HOLD, RELEASE, or WAIT.
        """
        if fish_x is None or zone_left is None or zone_right is None:
            return Action.WAIT

        zone_center = (zone_left + zone_right) / 2

        self._history.append((fish_x, timestamp))
        if len(self._history) > self._history_size:
            self._history.pop(0)

        # px/s estimate
        self._velocity = self._estimate_velocity()

        # predicted target
        target_x = fish_x
        if self._prediction_enabled and len(self._history) >= 2:
            lookahead_s = self._lookahead_ms / 1000.0
            target_x = fish_x + self._velocity * lookahead_s

        # target smoothing
        if hasattr(self, "_last_target_x") and self._last_target_x is not None:
            target_x = self._smoothing * self._last_target_x + (1.0 - self._smoothing) * target_x
        self._last_target_x = target_x

        diff = target_x - zone_center
        deadzone = self._deadzone

        # left edge clamp
        if zone_left <= self._edge_margin:
            action = Action.HOLD
        elif diff > deadzone:
            action = Action.HOLD
        elif diff < -deadzone:
            action = Action.RELEASE
        else:
            action = Action.WAIT

        self._last_action = action
        return action

    def _estimate_velocity(self) -> float:
        """Estimate fish horizontal velocity in px/s from history."""
        if len(self._history) < 2:
            return 0.0
        x_old, t_old = self._history[0]
        x_new, t_new = self._history[-1]
        dt = t_new - t_old
        if dt < 1e-6:
            return 0.0
        return (x_new - x_old) / dt

    def reset(self) -> None:
        """Reset all state. Call when fishing stops."""
        self._history.clear()
        self._velocity = 0.0
        self._last_action = Action.WAIT
        self._last_target_x = None
        logger.debug("Controller reset")

    @property
    def last_action(self) -> Action:
        return self._last_action

    @property
    def estimated_velocity(self) -> float:
        return self._velocity

    @property
    def prediction_target(self) -> Optional[int]:
        if self._prediction_enabled and len(self._history) >= 2:
            return int(self._last_target_x) if self._last_target_x is not None else None
        return None
