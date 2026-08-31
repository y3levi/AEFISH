import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import cv2
import pytest

from src.core.detector import Detector

PROJECT_ROOT = Path(__file__).parent.parent
PROFILE_PATH = PROJECT_ROOT / "src" / "config" / "profiles" / "default.json"
REAL_FRAME_PATH = PROJECT_ROOT / "scratch" / "debug_contours.png"
FIXTURES = Path(__file__).parent / "fixtures"

# Real in-game HSV colors measured on scratch/debug_contours.png
BAR_BG_HSV = (102, 230, 31)     # dark bar background
ZONE_HSV = (102, 255, 194)      # bright saturated blue zone fill
FISH_HSV = (103, 90, 229)       # light blue fish icon (free state)
FISH_HOVER_HSV = (0, 0, 255)    # white fish icon (zone touching it)


def hsv_to_bgr(hsv):
    px = np.uint8([[list(hsv)]])
    return cv2.cvtColor(px, cv2.COLOR_HSV2BGR)[0][0].tolist()


@pytest.fixture
def profile():
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def make_bar_frame(zone_x=30, zone_w=200, fish_x=None, w=400, h=37, fish_hover=False):
    """Synthetic minigame bar: dark background, blue zone, optional fish icon."""
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:, :] = hsv_to_bgr(BAR_BG_HSV)
    frame[10:25, zone_x:zone_x + zone_w] = hsv_to_bgr(ZONE_HSV)
    if fish_x is not None:
        # fish icon drawn last: on top of the zone when overlapping;
        # it turns white when the zone touches it
        color = FISH_HOVER_HSV if fish_hover else FISH_HSV
        frame[10:25, fish_x:fish_x + 15] = hsv_to_bgr(color)
    return frame


def test_zone_not_merged_with_dark_background(profile):
    # regression: the dark bar background used to fall inside the zone HSV
    # range, merging the whole bar into one giant rejected contour
    det = Detector(profile)
    res = det.detect(make_bar_frame(zone_x=30, zone_w=200, fish_x=300))
    assert res.zone_detected
    assert abs(res.zone_center - 130) <= 5
    assert abs(res.zone_left - 30) <= 5
    assert abs(res.zone_right - 230) <= 5


def test_fish_detected_on_dark_background(profile):
    det = Detector(profile)
    res = det.detect(make_bar_frame(zone_x=30, zone_w=200, fish_x=300))
    assert res.fish_detected
    assert abs(res.fish_x - 307) <= 5
    assert res.confidence == 1.0


def test_fish_detected_while_overlapping_zone(profile):
    # regression: the fish used to disappear the moment the zone reached it
    # (both masks matched blue, contours merged and got rejected)
    det = Detector(profile)
    res = det.detect(make_bar_frame(zone_x=30, zone_w=200, fish_x=120))
    assert res.fish_detected, "fish must stay detected on top of the zone"
    assert abs(res.fish_x - 127) <= 5
    assert res.confidence == 1.0


def test_zone_center_stable_when_fish_splits_it(profile):
    # the fish punches a hole through the zone mask; the close kernel must
    # rejoin both halves so zone_center does not jump to one half
    det = Detector(profile)
    res = det.detect(make_bar_frame(zone_x=30, zone_w=200, fish_x=120))
    assert res.zone_detected
    assert abs(res.zone_center - 130) <= 10


def test_white_hover_fish_detected_on_zone(profile):
    # regression: the fish icon turns WHITE when the zone touches it; the
    # hover mask must keep it detected through the whole contact
    det = Detector(profile)
    res = det.detect(make_bar_frame(zone_x=30, zone_w=200, fish_x=120, fish_hover=True))
    assert res.fish_detected, "white hover fish must stay detected on the zone"
    assert abs(res.fish_x - 127) <= 5
    assert res.zone_detected
    assert res.confidence == 1.0


def test_partial_detection_confidence(profile):
    det = Detector(profile)
    # zone only, no fish
    res = det.detect(make_bar_frame(zone_x=30, zone_w=200, fish_x=None))
    assert res.zone_detected and not res.fish_detected
    assert res.confidence == 0.5
    # empty bar
    res = det.detect(make_bar_frame(zone_x=30, zone_w=0, fish_x=None))
    assert res.confidence == 0.0


@pytest.mark.skipif(not (FIXTURES / "fish_free.png").exists(), reason="fixture not available")
def test_real_capture_fish_free(profile):
    # real capture: light blue fish away from the zone
    img = cv2.imread(str(FIXTURES / "fish_free.png"))
    det = Detector(profile)
    res = det.detect(img)
    assert res.fish_detected
    assert abs(res.fish_x - 388) <= 6
    assert res.zone_detected
    assert abs(res.zone_center - 135) <= 10
    assert res.confidence == 1.0


@pytest.mark.skipif(not (FIXTURES / "fish_contact.png").exists(), reason="fixture not available")
def test_real_capture_fish_contact(profile):
    # real capture: WHITE fish while the zone is on top of it — this frame
    # used to drop detection to 0% at the exact moment of success
    img = cv2.imread(str(FIXTURES / "fish_contact.png"))
    det = Detector(profile)
    res = det.detect(img)
    assert res.fish_detected, "fish must stay detected while in contact"
    assert abs(res.fish_x - 762) <= 10
    assert res.zone_detected
    assert abs(res.zone_center - 674) <= 10
    assert res.confidence == 1.0


@pytest.mark.skipif(not REAL_FRAME_PATH.exists(), reason="real frame not available")
def test_real_frame_detection(profile):
    # bar strip cropped from a real annotated screenshot (same 913x37 shape
    # as the calibrated capture region)
    img = cv2.imread(str(REAL_FRAME_PATH))
    crop = img[78:115, 20:933]
    det = Detector(profile)
    res = det.detect(crop)
    assert res.fish_detected
    assert abs(res.fish_x - 599) <= 5
    assert res.zone_detected
    assert abs(res.zone_center - 192) <= 10
    assert res.confidence == 1.0
