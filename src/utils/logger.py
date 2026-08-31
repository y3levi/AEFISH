"""Centralized logging setup for the application."""
import logging
import sys
from pathlib import Path
from datetime import datetime

_initialized = False
_log_dir = Path("logs")


def setup_logging(save_logs: bool = True) -> None:
    """Configure root logger. Call once at startup."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)-25s %(message)s",
        datefmt="%H:%M:%S",
    )

    handlers: list[logging.Handler] = []

    # console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.DEBUG)
    handlers.append(console_handler)

    # file handler
    if save_logs:
        try:
            _log_dir.mkdir(parents=True, exist_ok=True)
            log_file = _log_dir / f"aefish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(fmt)
            file_handler.setLevel(logging.DEBUG)
            handlers.append(file_handler)
        except OSError as e:
            print(f"[logger] Could not create log file: {e}")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for h in handlers:
        root.addHandler(h)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. setup_logging() must be called first."""
    return logging.getLogger(name)
