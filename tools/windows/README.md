### Windows file association

To open `.sfg` files with SignalFlowGrapher and show the app icon in Windows Explorer, run:

- To use the system-wide python executable, use:  `powershell -ExecutionPolicy Bypass -File .\tools\windows\register_sfg_association.ps1`
- Or to specify the path to the `pythonw.exe` excutable, run:  `powershell -ExecutionPolicy Bypass -File .\tools\windows\register_sfg_association.ps1 -PythonLauncherPath C:\path\to\pythonw.exe`

This creates a per-user association for `.sfg` files, uses `src\main\icons\Icon.ico` as the file-type icon, and creates a desktop shortcut named `SignalFlowGrapher.lnk`. To remove the association and shortcut again, run the same script with `-Uninstall`.

#### Virtual Environment

If a virtual environment is used to cleanly install the required packages, use the `-PythonLauncherPath` to pass over the python executable of the virtual environment.

E.g. if you have a virtual environment named `sfg_venv` in the home directory, run the script as following: `powershell -ExecutionPolicy Bypass -File .\tools\windows\register_sfg_association.ps1 -PythonLauncherPath $HOME\sfg_venv\Scripts\pythonw.exe`
