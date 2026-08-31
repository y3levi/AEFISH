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
