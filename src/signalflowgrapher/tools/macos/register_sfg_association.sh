#!/bin/bash
# Shell script to register the .sfg file association for SignalFlowGrapher on macOS.
# This improved version properly sets up the environment for double-click launching.
#
# Usage:
#   ./register_sfg_association.sh [--python-path /path/to/python3] [--uninstall]
#
# The script will automatically detect your Python environment and PySide6 installation.
# For best results, run this script from your activated virtual environment.

set -euo pipefail

# ---- Configuration ---------------------------------------------------
APP_NAME="SignalFlowGrapher"
BUNDLE_ID="com.signalflowgrapher.app"
EXTENSION="sfg"
MODULE_NAME="signalflowgrapher"

# ---- Argument parsing ---------------------------------------------------
UNINSTALL=0
PYTHON_PATH=""
FORCE=0

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
        --force|-f)
            FORCE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --uninstall              Remove the app bundle and file association"
            echo "  --python-path PATH       Use specific Python executable"
            echo "  --force, -f              Force recreation even if app exists"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

# ---- Locate files ---------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ICONS_MAC_DIR="$PACKAGE_ROOT/resources/icons/mac"

APP_DIR="$HOME/Applications/${APP_NAME}.app"
DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_PATH="$DESKTOP_DIR/${APP_NAME}.app"

# ---- Uninstall -----------------------------------------------------------
if [[ "$UNINSTALL" -eq 1 ]]; then
    # Remove shortcut
    if [[ -e "$SHORTCUT_PATH" || -L "$SHORTCUT_PATH" ]]; then
        rm -rf "$SHORTCUT_PATH"
        echo "✓ Removed desktop shortcut"
    fi

    # Remove app bundle
    if [[ -d "$APP_DIR" ]]; then
        rm -rf "$APP_DIR"
        echo "✓ Removed app bundle: $APP_DIR"
    fi

    # Unregister from Launch Services
    LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
    if [[ -x "$LSREGISTER" ]]; then
        "$LSREGISTER" -u "$APP_DIR" >/dev/null 2>&1 || true
        echo "✓ Unregistered from Launch Services"
    fi

    echo ""
    echo "✅ SignalFlowGrapher has been uninstalled."
    echo "   - App bundle removed"
    echo "   - Desktop shortcut removed"
    echo "   - File association removed"
    exit 0
fi

# ---- Find Python and PySide6 ---------------------------------------------
# Find the Python interpreter
if [[ -n "$PYTHON_PATH" ]]; then
    if [[ ! -x "$PYTHON_PATH" ]]; then
        echo "❌ Error: Python executable not found or not executable: $PYTHON_PATH" >&2
        exit 1
    fi
    PYTHON_EXE="$PYTHON_PATH"
else
    # Try to find Python3
    PYTHON_EXE="$(command -v python3 || true)"
    if [[ -z "$PYTHON_EXE" ]]; then
        echo "❌ Error: Could not find python3 on PATH." >&2
        echo "   Please activate your virtual environment or specify with --python-path" >&2
        exit 1
    fi
fi

echo "🔍 Using Python: $PYTHON_EXE"

# Verify PySide6 is installed
if ! "$PYTHON_EXE" -c "import PySide6; print(PySide6.__path__[0])" 2>/dev/null; then
    echo "❌ Error: PySide6 is not installed in this Python environment." >&2
    echo "   Please install it with: pip install PySide6" >&2
    exit 1
fi

# Get PySide6 installation path
PYSIDE6_PATH="$("$PYTHON_EXE" -c "import PySide6; print(PySide6.__path__[0])" 2>/dev/null)"
if [[ -z "$PYSIDE6_PATH" ]]; then
    echo "❌ Error: Could not determine PySide6 installation path." >&2
    exit 1
fi
echo "🔍 PySide6 found at: $PYSIDE6_PATH"

# Get site-packages directory
SITE_PACKAGES="$("$PYTHON_EXE" -c "import sys; print(sys.path[-1])" 2>/dev/null)"
if [[ -z "$SITE_PACKAGES" ]]; then
    # Fallback: try to find site-packages
    SITE_PACKAGES="$("$PYTHON_EXE" -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || echo "")"
fi
if [[ -z "$SITE_PACKAGES" ]]; then
    echo "❌ Error: Could not determine site-packages directory." >&2
    exit 1
fi
echo "🔍 Site-packages: $SITE_PACKAGES"

# Verify Qt platform plugin exists
QT_PLUGINS_DIR="$PYSIDE6_PATH/Qt/plugins"
QT_PLATFORM_PLUGIN="$QT_PLUGINS_DIR/platforms/libqcocoa.dylib"
if [[ ! -f "$QT_PLATFORM_PLUGIN" ]]; then
    # Try alternative location
    QT_PLATFORM_PLUGIN="$SITE_PACKAGES/PySide6/Qt/plugins/platforms/libqcocoa.dylib"
    if [[ ! -f "$QT_PLATFORM_PLUGIN" ]]; then
        echo "⚠️  Warning: Qt Cocoa platform plugin not found at expected location."
        echo "   Looking for: $QT_PLATFORM_PLUGIN"
        echo "   The app might still work, but could have display issues."
    fi
fi

# Verify the module exists
if ! "$PYTHON_EXE" -c "import $MODULE_NAME" 2>/dev/null; then
    echo "⚠️  Warning: Module '$MODULE_NAME' not found in Python path."
    echo "   Make sure you're in the right environment or the module is installed."
    echo "   Continuing anyway, but the app may not launch correctly."
fi

# ---- Build the app bundle ------------------------------------------------
echo ""
echo "📦 Building app bundle..."

# Remove existing app if forced
if [[ -d "$APP_DIR" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        rm -rf "$APP_DIR"
        echo "   Removed existing app bundle (--force)"
    else
        echo "⚠️  App bundle already exists at: $APP_DIR"
        echo "   Use --force to overwrite, or --uninstall to remove it first."
        exit 1
    fi
fi

# Create directory structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"
mkdir -p "$APP_DIR/Contents/Frameworks"

# ---- Create launcher script (main executable) ----------------------------
# This is the script that runs when the app is double-clicked
cat > "$APP_DIR/Contents/MacOS/${APP_NAME}" <<'EOF'
#!/bin/bash
# SignalFlowGrapher Launcher
# This script properly sets up the environment for double-click launching

# Get the app directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RESOURCES_DIR="$APP_DIR/Resources"

# Load environment configuration if it exists
if [[ -f "$RESOURCES_DIR/env.sh" ]]; then
    source "$RESOURCES_DIR/env.sh"
fi

# Find Python interpreter
# Priority: embedded Python > env.sh > PATH
if [[ -x "$RESOURCES_DIR/python/bin/python3" ]]; then
    PYTHON_EXE="$RESOURCES_DIR/python/bin/python3"
elif [[ -n "$PYTHON_EXE" && -x "$PYTHON_EXE" ]]; then
    # PYTHON_EXE might be set in env.sh
    :
else
    PYTHON_EXE="$(command -v python3 || echo "")"
fi

if [[ -z "$PYTHON_EXE" || ! -x "$PYTHON_EXE" ]]; then
    # Try common locations
    for p in /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
        if [[ -x "$p" ]]; then
            PYTHON_EXE="$p"
            break
        fi
    done
fi

if [[ ! -x "$PYTHON_EXE" ]]; then
    echo "ERROR: Could not find Python interpreter." >&2
    echo "Please ensure Python 3 is installed and available." >&2
    exit 1
fi

# Set up environment variables
export PYTHONUNBUFFERED=1
export QT_QPA_PLATFORM=cocoa

# Add site-packages to Python path if not already set
if [[ -n "$SITE_PACKAGES" ]]; then
    export PYTHONPATH="${SITE_PACKAGES}:${PYTHONPATH:-}"
fi

# Set Qt plugin paths if not already set
if [[ -n "$QT_PLUGIN_PATH" ]]; then
    export QT_PLUGIN_PATH
    export QT_QPA_PLATFORM_PLUGIN_PATH="${QT_PLUGIN_PATH}/platforms"
fi

# MacOS specific settings
export QTWEBENGINE_DISABLE_SANDBOX=1

# Add any additional libraries to the dynamic linker path
if [[ -n "$DYLD_LIBRARY_PATH" ]]; then
    export DYLD_LIBRARY_PATH
fi

# Debug: Uncomment to log launch
# exec >> "$HOME/Desktop/sfg_launch.log" 2>&1
# echo "=== SFG Launch at $(date) ==="
# echo "Python: $PYTHON_EXE"
# echo "PYTHONPATH: $PYTHONPATH"
# echo "QT_PLUGIN_PATH: $QT_PLUGIN_PATH"

# Launch the application
exec "$PYTHON_EXE" -m signalflowgrapher "$@"
EOF

chmod +x "$APP_DIR/Contents/MacOS/${APP_NAME}"

# ---- Create environment configuration file ------------------------------
# This file stores the environment settings for the launcher
cat > "$APP_DIR/Contents/Resources/env.sh" <<EOF
# Environment configuration for SignalFlowGrapher
# Generated by register_sfg_association.sh

# Python executable
PYTHON_EXE="$PYTHON_EXE"

# PySide6 paths
SITE_PACKAGES="$SITE_PACKAGES"
QT_PLUGIN_PATH="$QT_PLUGINS_DIR"

# Additional environment variables
export PYTHONUNBUFFERED=1
export QT_QPA_PLATFORM=cocoa
export PYTHONPATH="${SITE_PACKAGES}:${PYTHONPATH:-}"
export QT_PLUGIN_PATH="${QT_PLUGINS_DIR}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${QT_PLUGINS_DIR}/platforms"

# Dynamic linker paths (if needed)
# export DYLD_LIBRARY_PATH="${SITE_PACKAGES}/PySide6/Qt/lib:${DYLD_LIBRARY_PATH:-}"

# macOS specific
export QTWEBENGINE_DISABLE_SANDBOX=1
EOF

chmod 644 "$APP_DIR/Contents/Resources/env.sh"

# ---- Create a debug launcher (for troubleshooting) ----------------------
cat > "$APP_DIR/Contents/MacOS/debug.sh" <<'EOF'
#!/bin/bash
# Debug launcher - logs everything to ~/Desktop/sfg_debug.log
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source environment
if [[ -f "$APP_DIR/Contents/Resources/env.sh" ]]; then
    source "$APP_DIR/Contents/Resources/env.sh"
fi

# Log everything
LOG_FILE="$HOME/Desktop/sfg_debug.log"
echo "=== SignalFlowGrapher Debug Log ===" >> "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "Python: $PYTHON_EXE" >> "$LOG_FILE"
echo "PYTHONPATH: $PYTHONPATH" >> "$LOG_FILE"
echo "QT_PLUGIN_PATH: $QT_PLUGIN_PATH" >> "$LOG_FILE"
echo "Current directory: $(pwd)" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

exec "$PYTHON_EXE" -m signalflowgrapher "$@" 2>&1 | tee -a "$LOG_FILE"
EOF

chmod +x "$APP_DIR/Contents/MacOS/debug.sh"

# ---- Create Info.plist --------------------------------------------------
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
    <string>Icon</string>
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
            <string>Icon</string>
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

# ---- Create application icon --------------------------------------------
if [[ -d "$ICONS_MAC_DIR" ]]; then
    if command -v iconutil >/dev/null 2>&1; then
        echo "🎨 Creating application icon..."
        ICONSET_DIR="$(mktemp -d)/Icon.iconset"
        mkdir -p "$ICONSET_DIR"
        
        # Copy icon files (adjust sizes as needed)
        [[ -f "$ICONS_MAC_DIR/16.png" ]] && cp "$ICONS_MAC_DIR/16.png" "$ICONSET_DIR/icon_16x16.png"
        [[ -f "$ICONS_MAC_DIR/32.png" ]] && cp "$ICONS_MAC_DIR/32.png" "$ICONSET_DIR/icon_16x16@2x.png"
        [[ -f "$ICONS_MAC_DIR/32.png" ]] && cp "$ICONS_MAC_DIR/32.png" "$ICONSET_DIR/icon_32x32.png"
        [[ -f "$ICONS_MAC_DIR/64.png" ]] && cp "$ICONS_MAC_DIR/64.png" "$ICONSET_DIR/icon_32x32@2x.png"
        [[ -f "$ICONS_MAC_DIR/128.png" ]] && cp "$ICONS_MAC_DIR/128.png" "$ICONSET_DIR/icon_128x128.png"
        [[ -f "$ICONS_MAC_DIR/256.png" ]] && cp "$ICONS_MAC_DIR/256.png" "$ICONSET_DIR/icon_128x128@2x.png"
        [[ -f "$ICONS_MAC_DIR/256.png" ]] && cp "$ICONS_MAC_DIR/256.png" "$ICONSET_DIR/icon_256x256.png"
        [[ -f "$ICONS_MAC_DIR/512.png" ]] && cp "$ICONS_MAC_DIR/512.png" "$ICONSET_DIR/icon_256x256@2x.png"
        [[ -f "$ICONS_MAC_DIR/512.png" ]] && cp "$ICONS_MAC_DIR/512.png" "$ICONSET_DIR/icon_512x512.png"
        [[ -f "$ICONS_MAC_DIR/1024.png" ]] && cp "$ICONS_MAC_DIR/1024.png" "$ICONSET_DIR/icon_512x512@2x.png"
        
        iconutil -c icns "$ICONSET_DIR" -o "$APP_DIR/Contents/Resources/Icon.icns" 2>/dev/null || {
            echo "⚠️  Failed to create icon (iconutil error), using generic icon"
            # Create a generic icon placeholder
            touch "$APP_DIR/Contents/Resources/Icon.icns"
        }
        rm -rf "$(dirname "$ICONSET_DIR")"
        echo "   ✓ Icon created"
    else
        echo "⚠️  iconutil not found, skipping icon creation"
        echo "   Install Xcode Command Line Tools: xcode-select --install"
    fi
else
    echo "⚠️  Icon directory not found: $ICONS_MAC_DIR"
fi

# ---- Register with Launch Services --------------------------------------
echo "📝 Registering with Launch Services..."

LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [[ -x "$LSREGISTER" ]]; then
    "$LSREGISTER" -f "$APP_DIR" >/dev/null 2>&1 || true
    echo "   ✓ Registered app bundle"
fi

# Set as default opener for .sfg files
if command -v duti >/dev/null 2>&1; then
    duti -s "$BUNDLE_ID" "$EXTENSION" all >/dev/null 2>&1 || true
    echo "   ✓ Set as default opener for .${EXTENSION} files"
else
    echo "⚠️  duti not installed (brew install duti)"
    echo "   To set as default: right-click .${EXTENSION} file → Get Info → Open with → ${APP_NAME}"
fi

# ---- Create desktop shortcut --------------------------------------------
echo "📌 Creating desktop shortcut..."
mkdir -p "$DESKTOP_DIR"
rm -rf "$SHORTCUT_PATH"

if command -v osascript >/dev/null 2>&1; then
    # Create a proper Finder alias
    osascript -e "tell application \"Finder\" to make alias file to POSIX file \"$APP_DIR\" at POSIX file \"$DESKTOP_DIR\"" >/dev/null 2>&1 || true
    
    # Finder appends " alias" to the name
    GENERATED_ALIAS="$DESKTOP_DIR/${APP_NAME}.app alias"
    if [[ -e "$GENERATED_ALIAS" ]]; then
        mv "$GENERATED_ALIAS" "$SHORTCUT_PATH"
        echo "   ✓ Created Finder alias"
    else
        # Fallback: symlink
        ln -s "$APP_DIR" "$SHORTCUT_PATH"
        echo "   ✓ Created symlink (Finder alias fallback)"
    fi
else
    # Fallback: symlink
    ln -s "$APP_DIR" "$SHORTCUT_PATH"
    echo "   ✓ Created symlink"
fi

# ---- Final summary ------------------------------------------------------
echo ""
echo "✅ SignalFlowGrapher is now registered!"
echo ""
echo "📋 Summary:"
echo "   App bundle:  $APP_DIR"
echo "   Python:      $PYTHON_EXE"
echo "   PySide6:     $PYSIDE6_PATH"
echo "   Shortcut:    $SHORTCUT_PATH"
echo ""
echo "🚀 To launch:"
echo "   • Double-click the app from Finder"
echo "   • Double-click the desktop shortcut"
echo "   • Open a .sfg file (if associated)"
echo ""
echo "🐛 For debugging:"
echo "   • Run: $APP_DIR/Contents/MacOS/debug.sh"
echo "   • Check: ~/Desktop/sfg_debug.log"
echo "   • Or run from Terminal: $PYTHON_EXE -m signalflowgrapher"
echo ""
echo "💡 If the app doesn't launch:"
echo "   1. Check the debug log: ~/Desktop/sfg_debug.log"
echo "   2. Make sure PySide6 is installed: pip install PySide6"
echo "   3. Try: $APP_DIR/Contents/MacOS/debug.sh"
echo "   4. Check macOS privacy settings for the app"