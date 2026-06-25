#!/bin/bash
# Shell script to register the .sfg file association for SignalFlowGrapher on Linux.
# Follows the freedesktop.org specs (.desktop files, shared-mime-info, xdg-mime) so it
# works across GNOME, KDE, XFCE and other freedesktop-compliant desktop environments.
# Usage:
# To register the .sfg file ending using the python3 found on PATH, run this script without arguments:
#     ./register_sfg_association.sh
# To register the .sfg file ending with a specific python3 executable, pass its path:
#     ./register_sfg_association.sh --python-path /path/to/python3
# This script also creates a per-user desktop launcher named SignalFlowGrapher.desktop.
# To remove the file association and shortcut, run this script with the --uninstall flag:
#     ./register_sfg_association.sh --uninstall
# Note: This script expects to be in the tools/linux directory of the repository. If you move it,
# you may need to adjust the paths to the icon and main script. You can execute this script from
# any location, but it will look for the repository files relative to its own location.

set -euo pipefail

# ---- Argument parsing ---------------------------------------------------
UNINSTALL=0
PYTHON_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall)
            UNINSTALL=1
            shift
            ;;
        --python-path)
            PYTHON_PATH="$2"
            shift 2
            ;;
        --python-path=*)
            PYTHON_PATH="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--uninstall] [--python-path /path/to/python3]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

# ---- Locate repository files we need: the app icons and the Python entrypoint. ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ICONS_LINUX_DIR="$PACKAGE_ROOT/resources/icons/linux"
ICON_SIZES=(128 256 512 1024)
INVOCATION="-m signalflowgrapher"

APP_NAME="SignalFlowGrapher"
APP_ID="signalflowgrapher"
MIME_TYPE="application/x-signalflowgrapher-sfg"
EXTENSION="sfg"

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DESKTOP_FILE_DIR="$DATA_HOME/applications"
DESKTOP_FILE_PATH="$DESKTOP_FILE_DIR/${APP_ID}.desktop"
MIME_PACKAGE_DIR="$DATA_HOME/mime/packages"
MIME_PACKAGE_PATH="$MIME_PACKAGE_DIR/${APP_ID}.xml"

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
SHORTCUT_PATH="$DESKTOP_DIR/${APP_NAME}.desktop"

# ---- Uninstall -----------------------------------------------------------
if [[ "$UNINSTALL" -eq 1 ]]; then
    if [[ -f "$DESKTOP_FILE_PATH" ]]; then
        rm -f "$DESKTOP_FILE_PATH"
        echo "Removed application entry: $DESKTOP_FILE_PATH"
    fi

    if [[ -f "$MIME_PACKAGE_PATH" ]]; then
        rm -f "$MIME_PACKAGE_PATH"
        echo "Removed MIME definition: $MIME_PACKAGE_PATH"
    fi

    for size in "${ICON_SIZES[@]}"; do
        icon_path="$DATA_HOME/icons/hicolor/${size}x${size}/apps/${APP_ID}.png"
        if [[ -f "$icon_path" ]]; then
            rm -f "$icon_path"
            echo "Removed icon: $icon_path"
        fi
    done

    if [[ -f "$SHORTCUT_PATH" ]]; then
        rm -f "$SHORTCUT_PATH"
        echo "Removed desktop shortcut: $SHORTCUT_PATH"
    fi

    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database "$DATA_HOME/mime" >/dev/null 2>&1 || true
    fi
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_FILE_DIR" >/dev/null 2>&1 || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
    fi

    echo "SignalFlowGrapher file association removed for .${EXTENSION}"
    exit 0
fi

# ---- Find a usable Python interpreter -------------------------------------
if [[ -n "$PYTHON_PATH" ]]; then
    if [[ ! -x "$PYTHON_PATH" ]]; then
        echo "Python executable not found or not executable: $PYTHON_PATH" >&2
        exit 1
    fi
    PYTHON_EXE="$PYTHON_PATH"
else
    PYTHON_EXE="$(command -v python3 || true)"
    if [[ -z "$PYTHON_EXE" ]]; then
        echo "Could not find python3 on PATH. Activate the environment that contains the" >&2
        echo "GUI runtime, or pass --python-path /path/to/python3, then run this script again." >&2
        exit 1
    fi
fi

# ---- Install the app icon into the hicolor icon theme at every size we have ----
if [[ ! -d "$ICONS_LINUX_DIR" ]]; then
    echo "Icon directory not found: $ICONS_LINUX_DIR" >&2
    exit 1
fi

ICON_NAME="$APP_ID"
for size in "${ICON_SIZES[@]}"; do
    icon_dest_dir="$DATA_HOME/icons/hicolor/${size}x${size}/apps"
    mkdir -p "$icon_dest_dir"
    cp "$ICONS_LINUX_DIR/${size}.png" "$icon_dest_dir/${ICON_NAME}.png"
done

# ---- Register the MIME type for .sfg files ----
mkdir -p "$MIME_PACKAGE_DIR"
cat > "$MIME_PACKAGE_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="${MIME_TYPE}">
        <comment>SignalFlowGrapher file</comment>
        <glob pattern="*.${EXTENSION}"/>
        <icon name="${ICON_NAME}"/>
    </mime-type>
</mime-info>
EOF

if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database "$DATA_HOME/mime" >/dev/null 2>&1
else
    echo "Warning: 'update-mime-database' not found; the .${EXTENSION} MIME type may not" >&2
    echo "be picked up until it is run manually (it ships with shared-mime-info)." >&2
fi

# ---- Create the .desktop application entry ----
mkdir -p "$DESKTOP_FILE_DIR"
cat > "$DESKTOP_FILE_PATH" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=Signal flow graph editor
Exec=${PYTHON_EXE} ${INVOCATION} %f
Terminal=false
MimeType=${MIME_TYPE};
Categories=Education;Science;Engineering;
Icon=${ICON_NAME}
EOF
chmod +x "$DESKTOP_FILE_PATH"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_FILE_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi

# ---- Make this application the default for the .sfg MIME type, per-user ----
if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default "${APP_ID}.desktop" "$MIME_TYPE"
else
    echo "Warning: 'xdg-mime' not found; could not set ${APP_NAME} as the default .${EXTENSION}" >&2
    echo "handler automatically. Install xdg-utils, or set the default manually from your" >&2
    echo "file manager's 'Open With' dialog." >&2
fi

# ---- Create a desktop shortcut ----
mkdir -p "$DESKTOP_DIR"
cp "$DESKTOP_FILE_PATH" "$SHORTCUT_PATH"
chmod +x "$SHORTCUT_PATH"
# Many file managers (e.g. GNOME Files/Nautilus) require the launcher to be marked as
# trusted before it will run directly rather than just opening as text.
if command -v gio >/dev/null 2>&1; then
    gio set "$SHORTCUT_PATH" metadata::trusted true >/dev/null 2>&1 || true
fi

echo "SignalFlowGrapher is now the default app for .${EXTENSION} files in this Linux account."
echo "Application entry: $DESKTOP_FILE_PATH"
echo "Python: $PYTHON_EXE $INVOCATION"
echo "Shortcut: $SHORTCUT_PATH"
