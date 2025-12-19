import logging
import logging.config
import argparse
from os import path
import sys
from importlib import resources
from PySide6.QtWidgets import QApplication
from PySide6 import QtCore
from signalflowgrapher.containers import MainWindows

if __name__ == '__main__':
    # Instantiate ApplicationContext
    # NOTE: fbs ApplicationContext removed, importlib.resources is used instead

    # Init logger
    logger = logging.getLogger(__name__)

    # fbs get_resource replacement using importlib.resources
    with resources.path("signalflowgrapher.resources", "logging.conf") as logconfig:
        logging.config.fileConfig(
            str(logconfig),
            disable_existing_loggers=False
        )

    logger.info("Starting application")

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, help='Optional language name')
    args = parser.parse_args()

    app = QApplication([])

    # Set language by command line argument.  This is not done through the
    # application context yet because it anyway only works on the command line
    if (args.language):
        with resources.path(
            "signalflowgrapher.resources.translations",
            f"{args.language}.qm"
        ) as language_file:

            if (path.exists(language_file)):
                logger.debug("Using translation file: %s", language_file)
                translator = QtCore.QTranslator()
                translator.load(str(language_file))
                app.installTranslator(translator)
            else:
                print("Language file %s not found" % language_file)
                exit(2)

    window = MainWindows.main_window()
    window.show()

    # Invoke QApplication event loop
    exit_code = app.exec()
    sys.exit(exit_code)

# Review comments 08/23: There was a "Configure PyQt" here that has been moved
# to # main_window.py, mainly to make it possible to get this file flake8
# clean.
