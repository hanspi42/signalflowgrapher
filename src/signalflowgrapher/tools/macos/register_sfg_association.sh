#!/bin/bash
# Shell script to register the .sfg file association for SignalFlowGrapher on macOS.
# Usage:
# To register the .sfg file ending using the python3 found on PATH, run this script without arguments:
#     ./register_sfg_association.sh
# To register the .sfg file ending with a specific python3 executable, pass its path:
#     ./register_sfg_association.sh --python-path /path/to/python3
# This script also creates a per-user desktop alias named "SignalFlowGrapher".
# To remove the file association, the launcher app, and the shortcut, run this script with the --uninstall flag:
#     ./register_sfg_association.sh --uninstall
# Note: This script expects to be in the tools/macos directory of the repository. If you move it, you
# may need to adjust the paths to the icon and main script. You can execute this script from any
# location, but it will look for the repository files relative to its own location.

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
ICONS_MAC_DIR="$PACKAGE_ROOT/resources/icons/mac"
INVOCATION="-m signalflowgrapher"

APP_NAME="SignalFlowGrapher"
BUNDLE_ID="com.signalflowgrapher.app"
EXTENSION="sfg"
APP_DIR="$HOME/Applications/${APP_NAME}.app"
DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_PATH="$DESKTOP_DIR/${APP_NAME}.app"

# ---- Uninstall -----------------------------------------------------------
if [[ "$UNINSTALL" -eq 1 ]]; then
    # Remove the shortcut first: once the app bundle is deleted, a dangling symlink
    # shortcut would no longer satisfy a plain "-e" existence check.
    if [[ -e "$SHORTCUT_PATH" || -L "$SHORTCUT_PATH" ]]; then
        rm -rf "$SHORTCUT_PATH"
        echo "Removed desktop shortcut: $SHORTCUT_PATH"
    fi

    if [[ -d "$APP_DIR" ]]; then
        rm -rf "$APP_DIR"
        echo "Removed launcher app: $APP_DIR"
    fi

    # Tell Launch Services to forget the bundle so Finder stops offering it.
    LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
    if [[ -x "$LSREGISTER" ]]; then
        "$LSREGISTER" -u "$APP_DIR" >/dev/null 2>&1 || true
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

if [[ ! -d "$ICONS_MAC_DIR" ]]; then
    echo "Icon directory not found: $ICONS_MAC_DIR" >&2
    exit 1
fi

if ! command -v iconutil >/dev/null 2>&1; then
    echo "'iconutil' was not found. It ships with Xcode/Command Line Tools and is required" >&2
    echo "to build the .icns app icon. Install the Command Line Tools (xcode-select --install)" >&2
    echo "and re-run this script." >&2
    exit 1
fi

# Build the .icns app icon directly from the pre-sized PNGs in resources/icons/mac.
# Each source size doubles as the "@1x" of one slot and the "@2x" of the slot half its size.
ICONSET_DIR="$(mktemp -d)/Icon.iconset"
mkdir -p "$ICONSET_DIR"
cp "$ICONS_MAC_DIR/128.png" "$ICONSET_DIR/icon_128x128.png"
cp "$ICONS_MAC_DIR/256.png" "$ICONSET_DIR/icon_128x128@2x.png"
cp "$ICONS_MAC_DIR/256.png" "$ICONSET_DIR/icon_256x256.png"
cp "$ICONS_MAC_DIR/512.png" "$ICONSET_DIR/icon_256x256@2x.png"
cp "$ICONS_MAC_DIR/512.png" "$ICONSET_DIR/icon_512x512.png"
cp "$ICONS_MAC_DIR/1024.png" "$ICONSET_DIR/icon_512x512@2x.png"

mkdir -p "$APP_DIR/Contents/Resources"
iconutil -c icns "$ICONSET_DIR" -o "$APP_DIR/Contents/Resources/Icon.icns"
BUNDLE_ICON_NAME="Icon.icns"

# ---- Build a minimal .app bundle that macOS uses for the file association ----
mkdir -p "$APP_DIR/Contents/MacOS"

# Launcher script invoked by macOS when a .sfg file is opened or the app is double-clicked.
cat > "$APP_DIR/Contents/MacOS/${APP_NAME}" <<EOF
#!/bin/bash
exec "$PYTHON_EXE" $INVOCATION "\$@"
EOF
chmod +x "$APP_DIR/Contents/MacOS/${APP_NAME}"

# Info.plist declares the document type so Finder/Launch Services associate .sfg with this app.
cat > "$APP_DIR/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>${BUNDLE_ICON_NAME}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>SignalFlowGrapher file</string>
            <key>CFBundleTypeRole</key>
            <string>Editor</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>${BUNDLE_ID}.${EXTENSION}</string>
            </array>
            <key>CFBundleTypeIconFile</key>
            <string>${BUNDLE_ICON_NAME}</string>
        </dict>
    </array>
    <key>UTExportedTypeDeclarations</key>
    <array>
        <dict>
            <key>UTTypeIdentifier</key>
            <string>${BUNDLE_ID}.${EXTENSION}</string>
            <key>UTTypeDescription</key>
            <string>SignalFlowGrapher file</string>
            <key>UTTypeConformsTo</key>
            <array>
                <string>public.data</string>
            </array>
            <key>UTTypeTagSpecification</key>
            <dict>
                <key>public.filename-extension</key>
                <array>
                    <string>${EXTENSION}</string>
                </array>
            </dict>
        </dict>
    </array>
</dict>
</plist>
EOF

# ---- Register the bundle with Launch Services so Finder picks it up immediately. ----
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [[ -x "$LSREGISTER" ]]; then
    "$LSREGISTER" -f "$APP_DIR" >/dev/null 2>&1 || true
fi

# Ask Launch Services to make this app the default opener for .sfg, per-user.
if command -v duti >/dev/null 2>&1; then
    duti -s "$BUNDLE_ID" "$EXTENSION" all >/dev/null 2>&1 || true
else
    echo "Note: 'duti' is not installed, so the .sfg default-app association could not be" >&2
    echo "set automatically. The app has been registered with Launch Services; to finish," >&2
    echo "right-click any .sfg file in Finder, choose Get Info > Open with > ${APP_NAME}.app," >&2
    echo "and click 'Change All...'. Alternatively, install duti (e.g. 'brew install duti')" >&2
    echo "and re-run this script." >&2
fi

# ---- Create a desktop shortcut (an alias to the app bundle) ----
mkdir -p "$DESKTOP_DIR"
rm -rf "$SHORTCUT_PATH"
if command -v osascript >/dev/null 2>&1; then
    osascript -e "tell application \"Finder\" to make alias file to POSIX file \"$APP_DIR\" at POSIX file \"$DESKTOP_DIR\"" >/dev/null 2>&1 || true
    GENERATED_ALIAS="$DESKTOP_DIR/${APP_NAME}.app alias"
    if [[ -e "$GENERATED_ALIAS" ]]; then
        mv "$GENERATED_ALIAS" "$SHORTCUT_PATH"
    fi
fi
if [[ ! -e "$SHORTCUT_PATH" ]]; then
    # Fallback: a symlink works for double-click launching even if it isn't a true Finder alias.
    ln -s "$APP_DIR" "$SHORTCUT_PATH"
fi

echo "SignalFlowGrapher is now registered as an opener for .${EXTENSION} files in this macOS account."
echo "App bundle: $APP_DIR"
echo "Python: $PYTHON_EXE $INVOCATION"
echo "Shortcut: $SHORTCUT_PATH"
