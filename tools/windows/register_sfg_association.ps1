# PowerShell script to register the .sfg file association for SignalFlowGrapher on Windows.
# Written by @gfcwfzkm on GitHub.
# Usage:
# To register the .sfg file ending, run this script without arguments:
#     powershell -ExecutionPolicy Bypass -File register_sfg_association.ps1
# To register the .sfg file ending with a specific pythonw/pyw executable, pass its path:
#     powershell -ExecutionPolicy Bypass -File register_sfg_association.ps1 -PythonLauncherPath C:\path\to\pythonw.exe
# This script also creates a per-user desktop shortcut named SignalFlowGrapher.lnk.
# To remove the file association, run this script with the -Uninstall flag:
#     powershell -ExecutionPolicy Bypass -File register_sfg_association.ps1 -Uninstall
# Note: This script expects to be in the tools/windows directory of the repository. If you move it, you may need to adjust the paths to the icon and main script. You can execute this script from any location, but it will look for the repository files relative to its own location.

param(
    [switch]$Uninstall,
    [string]$PythonLauncherPath
)

# Find the repository files we need: the app icon and the Python entrypoint.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
$iconPath = Join-Path $repoRoot 'src\main\icons\Icon.ico'
$mainScript = Join-Path $repoRoot 'src\main\python\main.py'

if (-not (Test-Path $iconPath)) {
    throw "Icon file not found: $iconPath"
}

if (-not (Test-Path $mainScript)) {
    throw "Launcher script not found: $mainScript"
}

# Check for the GUI Python launcher to avoid flashing a console window when opening files.
$pythonLauncher = $null
if ($PythonLauncherPath) {
    if (-not (Test-Path $PythonLauncherPath)) {
        throw "Python launcher not found: $PythonLauncherPath"
    }

    $pythonLauncher = (Resolve-Path $PythonLauncherPath).Path
} else {
    foreach ($candidate in @('pythonw.exe', 'pyw.exe')) {
        try {
            $pythonLauncher = (Get-Command $candidate -ErrorAction Stop).Source
            break
        } catch {
        }
    }

    if (-not $pythonLauncher) {
        throw 'Could not find pythonw.exe or pyw.exe on PATH. Activate the environment that contains the GUI runtime, or pass -PythonLauncherPath to the launcher executable, then run this script again.'
    }
}

$extension = '.sfg'
$progId = 'SignalFlowGrapher.SFG'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'SignalFlowGrapher.lnk'
$classesRoot = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Classes', $true)

$wshShell = New-Object -ComObject WScript.Shell

if ($Uninstall) {
    # Remove the file association if it was created by this script.
    $extensionKey = $classesRoot.OpenSubKey($extension, $true)
    if ($extensionKey) {
        $currentValue = $extensionKey.GetValue('')
        if ($currentValue -eq $progId) {
            try {
                $classesRoot.DeleteSubKeyTree($extension)
            } catch {
                Write-Host "Failed to delete registry key for $extension. You may need to remove it manually."
            }
        }
        $extensionKey.Close()
    }

    try {
        $classesRoot.DeleteSubKeyTree($progId)
    } catch {
        Write-Host "No registry entry found for $progId, skipping deletion."
    }

    if (Test-Path $shortcutPath) {
        try {
            Remove-Item $shortcutPath -Force
        } catch {
            Write-Host "Failed to delete shortcut at $shortcutPath. You may need to remove it manually."
        }
    }

    Write-Host 'SignalFlowGrapher file association removed for .sfg'
    exit 0
}

# Create the file type entry used by Windows Explorer for .sfg files.
$progKey = $classesRoot.CreateSubKey($progId)
$progKey.SetValue('', 'SignalFlowGrapher file')

# Set the icon for .sfg files to the bundled application icon.
$defaultIconKey = $progKey.CreateSubKey('DefaultIcon')
$defaultIconKey.SetValue('', "$iconPath,0")
$defaultIconKey.Close()

# Define the action for opening .sfg files in Windows Explorer.
$shellKey = $progKey.CreateSubKey('shell')
$openKey = $shellKey.CreateSubKey('open')
$commandKey = $openKey.CreateSubKey('command')
$commandKey.SetValue('', "`"$pythonLauncher`" `"$mainScript`" `"%1`"")
$commandKey.Close()
$openKey.Close()
$shellKey.Close()
$progKey.Close()

# Create the file extension entry in the registry for .sfg files.
$extensionKey = $classesRoot.CreateSubKey($extension)
$extensionKey.SetValue('', $progId)
$extensionKey.Close()

# Create a desktop shortcut that launches SignalFlowGrapher with the selected Python launcher.
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonLauncher
$shortcut.Arguments = "`"$mainScript`""
$shortcut.WorkingDirectory = $repoRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = 'SignalFlowGrapher'
$shortcut.Save()

# Confirm the association is active for this Windows account.
Write-Host 'SignalFlowGrapher is now the default app for .sfg files in this Windows account.'
Write-Host "Icon: $iconPath"
Write-Host "Command: `"$pythonLauncher`" `"$mainScript`" `"%1`""
Write-Host "Shortcut: $shortcutPath"