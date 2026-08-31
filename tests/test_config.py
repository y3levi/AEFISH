import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.config_manager import ConfigManager
from src.config.defaults import DEFAULT_CONFIG
import pytest

def test_load_defaults(tmp_path):
    config_file = tmp_path / "config.json"
    cm = ConfigManager(config_file)
    assert cm.get("detection", "deadzone") == DEFAULT_CONFIG["detection"]["deadzone"]

def test_get_nested(tmp_path):
    config_file = tmp_path / "config.json"
    cm = ConfigManager(config_file)
    assert isinstance(cm.get("detection", "deadzone"), int)

def test_set_and_save(tmp_path):
    config_file = tmp_path / "config.json"
    cm = ConfigManager(config_file)
    cm.set("detection", "deadzone", value=999)
    cm.save()
    
    cm2 = ConfigManager(config_file)
    assert cm2.get("detection", "deadzone") == 999

def test_get_region_default_none(tmp_path):
    config_file = tmp_path / "config.json"
    cm = ConfigManager(config_file)
    assert cm.get_region() is None

def test_set_region_persists(tmp_path):
    config_file = tmp_path / "config.json"
    cm = ConfigManager(config_file)
    region = {"x": 10, "y": 20, "width": 100, "height": 200}
    cm.set_region(region)
    
    cm2 = ConfigManager(config_file)
    assert cm2.get_region() == region
