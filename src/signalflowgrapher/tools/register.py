import sys
import subprocess
from importlib import resources

def main():
    if sys.platform != "win32":
        print("File association registration is presently only supported on Windows.")
        return

    with resources.path(
        "signalflowgrapher.tools.windows",
        "register_sfg_association.ps1"
    ) as ps1:
        print(f"Running {ps1} ...")
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
            check=True
        )