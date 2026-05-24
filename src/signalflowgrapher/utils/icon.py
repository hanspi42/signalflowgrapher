import platform
from importlib import resources
from PySide6.QtGui import QIcon


def set_app_icon(app, app_id: str = 'org.signalflowgrapher.app'):
    system = platform.system().lower()

    if 'windows' in system:
        candidates = ['icons/Icon.ico']
    elif 'darwin' in system:
        candidates = ['icons/mac/512.png', 'icons/mac/256.png']
    else:
        candidates = [
            'icons/linux/256.png', 'icons/linux/128.png',
            'icons/base/64.png']

    for rel in candidates:
        # Split into package + filename for importlib.resources
        parts = rel.rsplit('/', 1)
        if len(parts) == 2:
            subpkg = (
                'signalflowgrapher.resources.' + parts[0].replace('/', '.'))
            fname = parts[1]
        else:
            subpkg = 'signalflowgrapher.resources'
            fname = parts[0]

        try:
            with resources.path(subpkg, fname) as icon_path:
                if icon_path.exists():
                    app.setWindowIcon(QIcon(str(icon_path)))
                    return True
        except (FileNotFoundError, ModuleNotFoundError):
            continue

    return False
