import threading
import queue
import time
from typing import Optional
import cv2
import numpy as np
from src.core.detector import DetectionResult
from src.utils.logger import get_logger

logger = get_logger('debug_window')

WINDOW_NAME = 'AE Auto Fishing — Debug'

class DebugWindow:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue = queue.Queue(maxsize=1)
        self._last_action: str = 'WAIT'
        self._last_fps: float = 0.0

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("debug window started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        logger.info("debug window stopped")

    def update(self, result: DetectionResult, action: str = 'WAIT', fps: float = 0.0, mouse_state: str = 'UP', engine_phase: str = 'IDLE', prediction_target: Optional[int] = None) -> None:
        if not self.is_running:
            return
        # queue clear
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        
        try:
            self._queue.put_nowait((result, action, fps, mouse_state, engine_phase, prediction_target))
        except queue.Full:
            pass

    def _run(self) -> None:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        try:
            while not self._stop_event.is_set():
                try:
                    result, action, fps, mouse_state, engine_phase, prediction_target = self._queue.get(timeout=0.1)
                    if result.debug_frame is not None:
                        frame = self._draw_overlay(result.debug_frame.copy(), result, action, fps, mouse_state, engine_phase, prediction_target)
                        cv2.imshow(WINDOW_NAME, frame)
                except queue.Empty:
                    pass
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    self._stop_event.set()
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    self._stop_event.set()
                    break
        finally:
            cv2.destroyAllWindows()

    def _draw_overlay(self, frame: np.ndarray, result: DetectionResult, action: str, fps: float, mouse_state: str, engine_phase: str, prediction_target: Optional[int]) -> np.ndarray:
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (280, 275), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

        # compute distance
        if result.fish_x is not None and result.zone_center is not None:
            dist = result.fish_x - result.zone_center
            dist_str = f"+{dist}" if dist >= 0 else str(dist)
        else:
            dist_str = 'N/A'

        texts = [
            f"Phase: {engine_phase}",
            f"Fish X: {result.fish_x if result.fish_x is not None else 'N/A'}",
            f"Zone Left: {result.zone_left if result.zone_left is not None else 'N/A'}",
            f"Zone Right: {result.zone_right if result.zone_right is not None else 'N/A'}",
            f"Zone Center: {result.zone_center if result.zone_center is not None else 'N/A'}",
            f"Distance: {dist_str}",
            f"Action: {action}",
            f"Mouse: {mouse_state}",
            f"Pred Target: {prediction_target if prediction_target is not None else 'N/A'}",
            f"Confidence: {result.confidence:.2f}",
            f"FPS: {fps:.0f}",
        ]

        y = 22
        for text in texts:
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y += 23

        return frame

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
