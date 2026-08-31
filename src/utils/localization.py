"""localization module."""
import json
from pathlib import Path
from typing import Callable, List

_strings: dict = {}
_callbacks: List[Callable] = []
_current_lang: str = "en"
_locales_dir = Path(__file__).parent.parent / "locales"


def load(lang: str) -> None:
    global _strings, _current_lang
    path = _locales_dir / f"{lang}.json"
    if not path.exists():
        path = _locales_dir / "en.json"
        lang = "en"
    try:
        with open(path, "r", encoding="utf-8") as f:
            _strings = json.load(f)
        _current_lang = lang
    except Exception:
        _strings = {}
    for cb in list(_callbacks):
        try:
            cb()
        except Exception:
            pass


def t(key: str, **kwargs) -> str:
    val = _strings.get(key, key)
    if kwargs:
        try:
            val = val.format(**kwargs)
        except Exception:
            pass
    return val


def on_language_change(callback: Callable) -> None:
    if callback not in _callbacks:
        _callbacks.append(callback)


def current_lang() -> str:
    return _current_lang
