### Windows file association

To open `.sfg` files with SignalFlowGrapher and show the app icon in Windows Explorer, run:

- `powershell -ExecutionPolicy Bypass -File .\tools\windows\register_sfg_association.ps1`
- If you are using a virtual environment, pass the launcher explicitly: `powershell -ExecutionPolicy Bypass -File .\tools\windows\register_sfg_association.ps1 -PythonLauncherPath C:\path\to\pythonw.exe`

This creates a per-user association for `.sfg` files, uses `src\main\icons\Icon.ico` as the file-type icon, and creates a desktop shortcut named `SignalFlowGrapher.lnk`. To remove the association and shortcut again, run the same script with `-Uninstall`.
