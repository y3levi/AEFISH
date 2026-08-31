import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.controller import Controller, Action
import pytest

@pytest.fixture
def base_config():
    return {
        "detection": {"deadzone": 10},
        "controller": {"prediction": False, "smoothing": 0.5}
    }

def test_fish_right_returns_hold(base_config):
    ctrl = Controller(base_config)
    # zone center = 100, deadzone = 10, fish_x = 120 -> 120 - 100 = 20 > 10 -> HOLD
    action = ctrl.update(fish_x=120, zone_left=90, zone_right=110, timestamp=1.0)
    assert action == Action.HOLD

def test_fish_left_returns_release(base_config):
    ctrl = Controller(base_config)
    # zone center = 100, deadzone = 10, fish_x = 80 -> 80 - 100 = -20 < -10 -> RELEASE
    action = ctrl.update(fish_x=80, zone_left=90, zone_right=110, timestamp=1.0)
    assert action == Action.RELEASE

def test_fish_in_deadzone_returns_wait(base_config):
    ctrl = Controller(base_config)
    # zone center = 100, deadzone = 10, fish_x = 105 -> 105 - 100 = 5 -> WAIT
    action = ctrl.update(fish_x=105, zone_left=90, zone_right=110, timestamp=1.0)
    assert action == Action.WAIT

def test_velocity_estimation(base_config):
    ctrl = Controller(base_config)
    ctrl.update(fish_x=100, zone_left=90, zone_right=110, timestamp=1.0)
    ctrl.update(fish_x=110, zone_left=90, zone_right=110, timestamp=1.1)
    assert ctrl.estimated_velocity > 0

def test_reset_clears_history(base_config):
    ctrl = Controller(base_config)
    ctrl.update(fish_x=100, zone_left=90, zone_right=110, timestamp=1.0)
    ctrl.update(fish_x=110, zone_left=90, zone_right=110, timestamp=1.1)
    ctrl.reset()
    assert ctrl.estimated_velocity == 0.0
    assert ctrl.last_action == Action.WAIT

def test_none_inputs_return_wait(base_config):
    ctrl = Controller(base_config)
    action = ctrl.update(fish_x=None, zone_left=90, zone_right=110, timestamp=1.0)
    assert action == Action.WAIT


def _simulate_minigame(ctrl, fish_fn, seconds=6.0, fps=60,
                       accel=1500.0, vmax=600.0, zone_w=300, frame_w=913):
    """Simulate the minigame bar physics: HOLD accelerates the zone right,
    RELEASE accelerates it left, WAIT keeps the current mouse state."""
    dt = 1.0 / fps
    zone_center = 150.0
    zone_vel = 0.0
    pressed = False
    t = 0.0
    diffs = []
    for _ in range(int(seconds * fps)):
        t += dt
        fish = fish_fn(t)
        action = ctrl.update(fish_x=int(fish),
                             zone_left=int(zone_center - zone_w / 2),
                             zone_right=int(zone_center + zone_w / 2),
                             timestamp=t)
        if action == Action.HOLD:
            pressed = True
        elif action == Action.RELEASE:
            pressed = False
        zone_vel += (accel if pressed else -accel) * dt
        zone_vel = max(-vmax, min(vmax, zone_vel))
        zone_center += zone_vel * dt
        zone_center = max(zone_w / 2, min(frame_w - zone_w / 2, zone_center))
        diffs.append(fish - zone_center)
    return diffs


def test_converges_on_static_fish():
    # bug scenario: the zone must settle over the fish instead of drifting off
    cfg = {"detection": {"deadzone": 10}, "controller": {"prediction": True, "smoothing": 0.5}}
    ctrl = Controller(cfg)
    diffs = _simulate_minigame(ctrl, lambda t: 600.0)
    tail = diffs[120:]  # after 2s of settling
    assert max(abs(d) for d in tail) < 120, "zone must stay locked on the fish"


def test_tracks_moving_fish():
    import math
    cfg = {"detection": {"deadzone": 10}, "controller": {"prediction": True, "smoothing": 0.5}}
    ctrl = Controller(cfg)
    diffs = _simulate_minigame(ctrl, lambda t: 450 + 200 * math.sin(1.5 * t))
    tail = diffs[120:]
    assert max(abs(d) for d in tail) < 120, "zone must keep tracking a moving fish"
