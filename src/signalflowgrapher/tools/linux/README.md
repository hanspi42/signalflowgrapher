### Linux file association

To open `.sfg` files with SignalFlowGrapher and show the app icon in your file manager, run:

- To use the `python3` found on `PATH`, use: `./tools/linux/register_sfg_association.sh`
- Or to specify the path to a particular `python3` executable, run: `./tools/linux/register_sfg_association.sh --python-path /path/to/python3`

This follows the [freedesktop.org](https://www.freedesktop.org/wiki/Specifications/) specifications used by GNOME, KDE, XFCE, and most other Linux desktop environments:

- Installs a `.desktop` application entry to `~/.local/share/applications/signalflowgrapher.desktop`.
- Registers a custom MIME type for `.sfg` files via a shared-mime-info package in `~/.local/share/mime/packages/`.
- Installs `resources/icons/linux/{128,256,512,1024}.png` into the matching `~/.local/share/icons/hicolor/<size>x<size>/apps/` directories.
- Sets SignalFlowGrapher as the default handler for `.sfg` files for the current user via `xdg-mime`.
- Creates a desktop shortcut named `SignalFlowGrapher.desktop` in your Desktop folder.

To remove the association, application entry, and shortcut again, run the same script with `--uninstall`.

#### Requirements

This script relies on standard `xdg-utils` and `shared-mime-info` tools (`xdg-mime`, `xdg-user-dir`, `update-mime-database`, `update-desktop-database`), which are pre-installed on virtually all Linux desktop distributions. If any are missing, the script will still complete and print instructions for finishing the setup manually (e.g. via your file manager's "Open With" dialog).

#### Virtual environment

If you use a virtual environment to cleanly install the required packages, pass `--python-path` to point at the Python executable inside it.

E.g. if you have a virtual environment named `sfg_venv` in your home directory, run the script as follows: `./tools/linux/register_sfg_association.sh --python-path $HOME/sfg_venv/bin/python3`

#### Permissions

The script may need to be made executable first: `chmod +x ./tools/linux/register_sfg_association.sh`
