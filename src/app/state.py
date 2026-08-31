from enum import Enum
from typing import Callable, Optional, Dict, List
import threading


class AppStatus(Enum):
    IDLE = "idle"
    WAITING_FOR_GAME = "waiting_for_game"
    CALIBRATING = "calibrating"
    CASTING = "casting"
    WAITING_FOR_MINIGAME = "waiting_for_minigame"
    DETECTING = "detecting"
    FISHING = "fishing"
    RECAST = "recast"
    PAUSED = "paused"
    ERROR = "error"


STATUS_LABELS: Dict[AppStatus, str] = {
    AppStatus.IDLE: "Idle",
    AppStatus.WAITING_FOR_GAME: "Waiting for game",
    AppStatus.CALIBRATING: "Calibrating",
    AppStatus.CASTING: "Casting...",
    AppStatus.WAITING_FOR_MINIGAME: "Waiting for minigame",
    AppStatus.DETECTING: "Detecting",
    AppStatus.FISHING: "Fishing",
    AppStatus.RECAST: "Recasting...",
    AppStatus.PAUSED: "Paused",
    AppStatus.ERROR: "Error",
}


class AppState:
    """thread-safe app state."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = AppStatus.IDLE
        self._status_text = STATUS_LABELS[AppStatus.IDLE]
        self._confidence: float = 0.0
        self._region: Optional[dict] = None
        self._callbacks: Dict[str, List[Callable]] = {
            "status": [],
            "confidence": [],
            "region": [],
        }

    @property
    def status(self) -> AppStatus:
        with self._lock:
            return self._status

    @property
    def status_text(self) -> str:
        with self._lock:
            return self._status_text

    @property
    def confidence(self) -> float:
        with self._lock:
            return self._confidence

    @property
    def region(self) -> Optional[dict]:
        with self._lock:
            if self._region is None:
                return None
            return dict(self._region)

    @property
    def is_fishing(self) -> bool:
        with self._lock:
            return self._status == AppStatus.FISHING

    def set_status(self, status: AppStatus, custom_text: str = "") -> None:
        with self._lock:
            self._status = status
            self._status_text = custom_text if custom_text else STATUS_LABELS[status]
        self._notify("status", self.status, self.status_text)

    def set_confidence(self, value: float) -> None:
        with self._lock:
            self._confidence = value
        self._notify("confidence", self.confidence)

    def set_region(self, region: Optional[dict]) -> None:
        with self._lock:
            self._region = dict(region) if region else None
        self._notify("region", self.region)

    def add_callback(self, event: str, callback: Callable) -> None:
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _notify(self, event: str, *args) -> None:
        with self._lock:
            cbs = list(self._callbacks.get(event, []))
        for cb in cbs:
            try:
                cb(*args)
            except Exception:
                pass
