"""default configuration values."""

DEFAULT_CONFIG: dict = {
    "hotkeys": {
        "toggle": "f6",
        "emergency_stop": "f7",
    },
    "capture": {
        "monitor": 1,
        "region": None,
        "water_click_position": None,
        "fps": 60,
        "recast_timeout_s": 20.0,
        "recast_cooldown_s": 1.5,
        "simple_rod_mode": False,
    },
    "detection": {
        "profile": "default",
        "sensitivity": 0.7,
        "confidence_threshold": 0.6,
        "deadzone": 10,
        "lost_target_timeout_ms": 500,
        "fish_lost_timeout_ms": 1200,
    },
    "controller": {
        "prediction": True,
        "reaction_delay_ms": 0,
        "smoothing": 0.9,
        "edge_margin": 15,
    },
    "debug": {
        "enabled": False,
        "show_masks": False,
    },
    "ui": {
        "always_on_top": False,
        "language": "en",
    },
}
