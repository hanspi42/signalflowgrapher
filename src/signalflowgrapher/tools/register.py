import sys
import subprocess
from importlib import resources


def main():
    if sys.platform == "win32":
        with resources.path(
            "signalflowgrapher.tools.windows",
            "register_sfg_association.ps1"
        ) as script:
            print(f"Running {script} ...")
            subprocess.run(
                [
                    "powershell", "-ExecutionPolicy", "Bypass",
                    "-File", str(script)],
                check=True
            )
    elif sys.platform == "darwin":
        with resources.path(
            "signalflowgrapher.tools.macos",
            "register_sfg_association.sh"
        ) as script:
            print(f"Running {script} ...")
            subprocess.run(["bash", str(script)], check=True)
    elif sys.platform.startswith("linux"):
        with resources.path(
            "signalflowgrapher.tools.linux",
            "register_sfg_association.sh"
        ) as script:
            print(f"Running {script} ...")
            subprocess.run(["bash", str(script)], check=True)
    else:
        print(
            f"Registration is not yet supported on {sys.platform!r}.")
