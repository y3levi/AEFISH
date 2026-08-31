import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.app.state import AppState, AppStatus, STATUS_LABELS
from src.config.config_manager import ConfigManager
from src.utils import localization


def test_all_statuses_in_labels():
    for status in AppStatus:
        assert status in STATUS_LABELS, f"{status} missing from STATUS_LABELS"


def test_new_states_exist():
    assert AppStatus.CASTING.value == "casting"
    assert AppStatus.WAITING_FOR_MINIGAME.value == "waiting_for_minigame"
    assert AppStatus.RECAST.value == "recast"


def test_app_state_set_status():
    state = AppState()
    state.set_status(AppStatus.CASTING)
    assert state.status == AppStatus.CASTING
    assert state.status_text == STATUS_LABELS[AppStatus.CASTING]


def test_app_state_custom_text():
    state = AppState()
    state.set_status(AppStatus.ERROR, "custom error")
    assert state.status == AppStatus.ERROR
    assert state.status_text == "custom error"


def test_is_fishing_flag():
    state = AppState()
    assert not state.is_fishing
    state.set_status(AppStatus.FISHING)
    assert state.is_fishing
    state.set_status(AppStatus.RECAST)
    assert not state.is_fishing


def test_localization_load_en():
    localization.load("en")
    assert localization.t("status.fishing") == "Fishing"
    assert localization.t("status.casting") == "Casting..."
    assert localization.t("status.recast") == "Recasting..."
    assert localization.t("status.waiting_for_minigame") == "Waiting for minigame"
    assert localization.current_lang() == "en"


def test_localization_load_pt():
    localization.load("pt_BR")
    assert localization.t("status.fishing") == "Pescando"
    assert localization.t("status.casting") == "Lançando..."
    assert localization.current_lang() == "pt_BR"
    localization.load("en")  # restore


def test_localization_missing_key():
    localization.load("en")
    result = localization.t("nonexistent.key")
    assert result == "nonexistent.key"


def test_config_new_fields(tmp_path):
    cfg = ConfigManager(tmp_path / "config.json")
    assert cfg.get("capture", "water_click_position") is None
    assert cfg.get("capture", "recast_timeout_s") == 20.0
    assert cfg.get("capture", "recast_cooldown_s") == 1.5
    assert cfg.get("detection", "fish_lost_timeout_ms") == 1200
    assert cfg.get("ui", "always_on_top") == False
    assert cfg.get("ui", "language") == "en"


def test_engine_no_region_returns_false(tmp_path):
    from src.core.fishing_engine import FishingEngine
    cfg = ConfigManager(tmp_path / "config.json")
    state = AppState()
    engine = FishingEngine(cfg, state)
    result = engine.start()
    assert result == False
    assert state.status == AppStatus.ERROR


def test_left_edge_coordinates():
    from src.core.controller import Controller, Action
    cfg = {
        "detection": {"deadzone": 10},
        "controller": {"prediction": False, "smoothing": 0.0, "edge_margin": 0}
    }
    ctrl = Controller(cfg)
    
    # fish at zero
    action = ctrl.update(fish_x=0, zone_left=7, zone_right=17, timestamp=1.0)
    assert action == Action.RELEASE
    
    ctrl.reset()
    
    # zone at zero
    action = ctrl.update(fish_x=20, zone_left=0, zone_right=0, timestamp=1.1)
    assert action == Action.HOLD


def test_fish_sides_hold_release():
    from src.core.controller import Controller, Action
    cfg = {
        "detection": {"deadzone": 10},
        "controller": {"prediction": False, "smoothing": 0.9, "edge_margin": 0}
    }
    ctrl = Controller(cfg)
    
    # fish on right
    action = ctrl.update(fish_x=50, zone_left=20, zone_right=40, timestamp=1.0)
    assert action == Action.HOLD
    
    ctrl.reset()
    
    # fish on left
    action = ctrl.update(fish_x=5, zone_left=20, zone_right=40, timestamp=1.1)
    assert action == Action.RELEASE


def test_wait_neutral_state():
    from src.core.controller import Controller, Action
    cfg = {
        "detection": {"deadzone": 10},
        "controller": {"prediction": False, "smoothing": 0.9, "edge_margin": 0}
    }
    ctrl = Controller(cfg)
    
    # inside deadzone
    action = ctrl.update(fish_x=22, zone_left=20, zone_right=40, timestamp=1.0)
    assert action == Action.WAIT


def test_edge_margin_clamp():
    from src.core.controller import Controller, Action
    cfg = {
        "detection": {"deadzone": 10},
        "controller": {"prediction": False, "smoothing": 0.0}
    }
    ctrl = Controller(cfg)
    
    # target right of zone
    action = ctrl.update(fish_x=90, zone_left=10, zone_right=80, timestamp=1.0)
    assert action == Action.HOLD
    
    ctrl.reset()
    
    # target left of zone
    action = ctrl.update(fish_x=5, zone_left=20, zone_right=80, timestamp=1.1)
    assert action == Action.RELEASE


def test_localization_keys_resolve():
    localization.load("en")
    assert localization.t("settings.section.general") != "settings.section.general"
    assert localization.t("settings.detection.fps") != "settings.detection.fps"
    assert localization.t("settings.controller.deadzone") != "settings.controller.deadzone"
    assert localization.t("settings.diagnostics.test_mouse_desc") != "settings.diagnostics.test_mouse_desc"
    
    localization.load("pt_BR")
    assert localization.t("settings.section.general") != "settings.section.general"
    assert localization.t("settings.detection.fps") != "settings.detection.fps"
    localization.load("en")


def test_first_cast_phase_flow(tmp_path):
    from src.core.fishing_engine import FishingEngine
    cfg = ConfigManager(tmp_path / "config.json")
    
    # set region
    cfg.set("capture", "region", value={"x": 100, "y": 100, "width": 200, "height": 30})
    # set water pos
    cfg.set("capture", "water_click_position", value={"x": 500, "y": 500})
    cfg.save()
    
    state = AppState()
    engine = FishingEngine(cfg, state)
    
    # verify idle
    assert engine.phase == "IDLE"
    assert not engine.is_running()


def test_aspect_ratio_filter():
    from src.core.detector import Detector
    import numpy as np
    
    # create profile
    prof = {
        "fish_detection": {
            "enabled": True,
            "hsv_lower": [0, 0, 200],
            "hsv_upper": [180, 40, 255],
            "min_area": 10,
            "max_area": 3000,
            "min_aspect_ratio": 0.4,
            "max_aspect_ratio": 2.5
        }
    }
    det = Detector(prof)
    
    # create canvas
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # horizontal line contour
    # w=50, h=2 -> aspect_ratio=25.0
    frame[40:42, 10:60] = 255
    res = det.detect(frame)
    assert not res.fish_detected
    
    # square fish contour
    # w=10, h=10 -> aspect_ratio=1.0
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[40:50, 40:50] = 255
    res = det.detect(frame)
    assert res.fish_detected


def test_simple_rod_mode(tmp_path):
    cfg = ConfigManager(tmp_path / "config.json")
    
    # simple rod config
    assert cfg.get("capture", "simple_rod_mode") == False
    cfg.set("capture", "simple_rod_mode", value=True)
    cfg.save()
    assert cfg.get("capture", "simple_rod_mode") == True
