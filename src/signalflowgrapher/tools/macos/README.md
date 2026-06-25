### macOS file association

To open `.sfg` files with SignalFlowGrapher and show the app icon in Finder, run:

- To use the `python3` found on `PATH`, use: `./tools/macos/register_sfg_association.sh`
- Or to specify the path to a particular `python3` executable, run: `./tools/macos/register_sfg_association.sh --python-path /path/to/python3`

This creates a small `SignalFlowGrapher.app` launcher bundle in `~/Applications`, builds its `.icns` app icon from `resources/icons/mac/{128,256,512,1024}.png`, and creates a desktop alias named `SignalFlowGrapher.app`. To remove the association, the launcher app, and the shortcut again, run the same script with `--uninstall`.

Building the `.icns` icon requires `iconutil`, which ships with Xcode and the Xcode Command Line Tools (`xcode-select --install`).

#### Setting the default app

macOS does not provide a built-in command to set a per-extension default application. This script registers `SignalFlowGrapher.app` with Launch Services so it appears as an option, and will automatically set it as the default for `.sfg` files if [`duti`](https://github.com/moretension/duti) is installed (e.g. via `brew install duti`). Without `duti`, finish the setup manually once:

1. Right-click (or Control-click) any `.sfg` file in Finder and choose **Get Info**.
2. Under **Open with**, choose `SignalFlowGrapher.app`.
3. Click **Change All...** to apply it to every `.sfg` file.

#### Virtual environment

If you use a virtual environment to cleanly install the required packages, pass `--python-path` to point at the Python executable inside it.

E.g. if you have a virtual environment named `sfg_venv` in your home directory, run the script as follows: `./tools/macos/register_sfg_association.sh --python-path $HOME/sfg_venv/bin/python3`

#### Permissions

The script may need to be made executable first: `chmod +x ./tools/macos/register_sfg_association.sh`
