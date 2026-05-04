from pathlib import Path
import sys
import platform
from PySide6.QtGui import QIcon


def _find_icons_dir():
    here = Path(__file__).resolve()
    for p in here.parents:
        # common layout: <repo>/src/main/icons
        candidate = p / 'main' / 'icons'
        if candidate.exists():
            return candidate
        candidate2 = p / 'src' / 'main' / 'icons'
        if candidate2.exists():
            return candidate2
        # sometimes icons live next to this package
        candidate3 = p / 'icons'
        if candidate3.exists():
            return candidate3

    # Fallback to cwd-based layout
    cwd_candidate = Path.cwd() / 'src' / 'main' / 'icons'
    if cwd_candidate.exists():
        return cwd_candidate

    return None


def set_app_icon(app, app_id: str = 'org.signalflowgrapher.app'):
    """Set the application's window icon based on platform and available icons.

    Tries to locate the `icons` directory in the repository and chooses a
    suitable icon for the current platform. Also attempts to set the
    Windows AppUserModelID so the taskbar groups correctly.
    """
    icons_dir = _find_icons_dir()
    if icons_dir is None:
        return False

    system = platform.system().lower()
    icon_path = None

    if 'windows' in system:
        candidate = icons_dir / 'Icon.ico'
        if candidate.exists():
            icon_path = candidate
    elif 'darwin' in system:
        candidate = icons_dir / 'mac' / '512.png'
        if candidate.exists():
            icon_path = candidate
    else:
        # Linux and others: prefer large PNG in linux/ then base/
        candidate = icons_dir / 'linux' / '256.png'
        if candidate.exists():
            icon_path = candidate

    if icon_path is None:
        # fallback to base icons
        candidate = icons_dir / 'base' / '64.png'
        if candidate.exists():
            icon_path = candidate

    if icon_path is None:
        return False

    try:
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)
    except Exception:
        return False

    return True
