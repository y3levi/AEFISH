import sys
import subprocess
import shutil
from pathlib import Path

# build configuration

APP_NAME = "Anime Expeditions Auto Fishing"
ENTRY_POINT = "src/main.py"
ICON_PATH = "assets/Toki1ICO.ico"
DIST_DIR = "dist"
BUILD_DIR = "build"

# data files
DATAS = [
    ("src/config/profiles", "src/config/profiles"),
    ("src/locales", "src/locales"),
    ("assets", "assets"),
    ("config.json", "."),
]

# hidden imports
HIDDEN_IMPORTS = [
    "customtkinter",
    "mss",
    "cv2",
    "numpy",
    "pynput",
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "PIL",
]


def clean() -> None:
    for path in [DIST_DIR, BUILD_DIR, "*.spec"]:
        for p in Path(".").glob(path):
            if p.is_dir():
                shutil.rmtree(p)
            elif p.is_file():
                p.unlink()


def build(onefile: bool = False) -> None:
    icon = Path(ICON_PATH).resolve()

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AEFISH",
        "--windowed",
        "--noconfirm",
    ]

    if icon.exists():
        args += ["--icon", str(icon)]

    for src, dst in DATAS:
        if Path(src).exists():
            args += ["--add-data", f"{src}{';' if sys.platform == 'win32' else ':'}{dst}"]

    for imp in HIDDEN_IMPORTS:
        args += ["--hidden-import", imp]

    args += ["--collect-data", "customtkinter"]

    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    args.append(ENTRY_POINT)

    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    do_clean = "--clean" in sys.argv
    do_onefile = "--onefile" in sys.argv

    if do_clean:
        clean()

    build(onefile=do_onefile)
