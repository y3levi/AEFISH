"""
Anime Expeditions Auto Fishing
by y3levi

Entry point. Sets up sys.path and launches the Application.
"""
import sys
from pathlib import Path

# sys.path fix
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.application import Application


def main() -> None:
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
