from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np
import cv2
from src.utils.logger import get_logger

logger = get_logger("detector")


@dataclass
class DetectionResult:
    """Result of a single detection pass."""
    fish_x: Optional[int] = None
    fish_y: Optional[int] = None
    fish_bbox: Optional[Tuple[int, int, int, int]] = None
    zone_left: Optional[int] = None
    zone_right: Optional[int] = None
    zone_center: Optional[int] = None
    zone_bbox: Optional[Tuple[int, int, int, int]] = None
    confidence: float = 0.0
    debug_frame: Optional[np.ndarray] = None

    @property
    def fish_detected(self) -> bool:
        return self.fish_x is not None

    @property
    def zone_detected(self) -> bool:
        return self.zone_center is not None

    @property
    def both_detected(self) -> bool:
        return self.fish_detected and self.zone_detected


class Detector:
    """Visual detector using HSV color segmentation."""

    def __init__(self, profile: dict) -> None:
        self._profile = profile
        self._fish_cfg: dict = {}
        self._zone_cfg: dict = {}
        self._update_from_profile()

    def _update_from_profile(self) -> None:
        """Extract and cache detection parameters from profile."""
        self._fish_cfg = self._profile.get("fish_detection", {})
        self._zone_cfg = self._profile.get("zone_detection", {})

    def update_profile(self, profile: dict) -> None:
        """Hot-reload detection profile without recreating detector."""
        self._profile = profile
        self._update_from_profile()
        logger.debug("Detection profile updated")

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Run detection on a BGR frame. Returns DetectionResult."""
        result = DetectionResult()
        debug_frame = frame.copy()
        frame_h, frame_w = frame.shape[:2]

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        if self._fish_cfg.get("enabled", True):
            self._detect_fish(hsv, frame_w, frame_h, result)

        if self._zone_cfg.get("enabled", True):
            self._detect_zone(hsv, frame_w, frame_h, result)

        result.confidence = self._compute_confidence(result)

        self._draw_debug(debug_frame, result)
        result.debug_frame = debug_frame

        return result

    def _detect_fish(self, hsv: np.ndarray, frame_w: int, frame_h: int, result: DetectionResult) -> None:
        """Detect fish indicator using unified HSV mask + contours."""
        # The fish in Anime Expeditions is light blue!
        lower = np.array(self._fish_cfg.get("hsv_lower", [85, 40, 140]))
        upper = np.array(self._fish_cfg.get("hsv_upper", [125, 255, 255]))
        
        mask = cv2.inRange(hsv, lower, upper)
        # We don't want MORPH_OPEN because the fish is small
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_area = 0
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 10 <= area <= 2500:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / max(1, h)
                
                # Fish is roughly square
                if 0.5 <= aspect_ratio <= 2.5:
                    if area > best_area:
                        best = cnt
                        best_area = area

        if best is not None:
            x, y, w, h = cv2.boundingRect(best)
            M = cv2.moments(best)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2
            result.fish_x = cx
            result.fish_y = cy
            result.fish_bbox = (x, y, w, h)

    def _detect_zone(self, hsv: np.ndarray, frame_w: int, frame_h: int, result: DetectionResult) -> None:
        """Detect blue controllable zone using HSV mask + contours."""
        lower = np.array(self._zone_cfg.get("hsv_lower", [85, 40, 60]))
        upper = np.array(self._zone_cfg.get("hsv_upper", [135, 255, 255]))
        
        mask = cv2.inRange(hsv, lower, upper)
        # Close to connect split parts of the blue zone
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 100:
                x, y, w, h = cv2.boundingRect(cnt)
                # Zone must have reasonable height (at least 5% of frame) and not span entire screen
                if h < max(3, int(frame_h * 0.05)) or w > frame_w * 0.75:
                    continue
                # Zone is wide
                if w > h * 2:
                    if area > best_area:
                        best = cnt
                        best_area = area

        if best is not None:
            x, y, w, h = cv2.boundingRect(best)
            result.zone_left = x
            result.zone_right = x + w
            result.zone_center = x + w // 2
            result.zone_bbox = (x, y, w, h)

    def _compute_confidence(self, result: DetectionResult) -> float:
        """Compute a confidence score based on minigame elements detection."""
        if result.both_detected:
            # Enforce vertical alignment! The fish must be inside/near the zone vertically.
            zone_y_center = result.zone_bbox[1] + (result.zone_bbox[3] // 2)
            if abs(result.fish_y - zone_y_center) < 35:
                return 1.0
        return 0.0

    def _draw_debug(self, frame: np.ndarray, result: DetectionResult) -> None:
        """Draw detection annotations on debug frame."""
        # fish bbox
        if result.fish_bbox:
            x, y, w, h = result.fish_bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
            if result.fish_x is not None and result.fish_y is not None:
                cv2.circle(frame, (result.fish_x, result.fish_y), 5, (0, 255, 255), -1)
                cv2.putText(frame, f"Fish: {result.fish_x}", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # zone bbox
        if result.zone_bbox:
            x, y, w, h = result.zone_bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 100, 0), 2)
            if result.zone_center is not None:
                cv2.line(frame, (result.zone_center, y), (result.zone_center, y + h), (255, 100, 0), 2)
                cv2.putText(frame, f"Zone: {result.zone_center}", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 1)

        # confidence
        cv2.putText(frame, f"Confidence: {result.confidence:.2f}",
                    (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
