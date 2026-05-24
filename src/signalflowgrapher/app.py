from PySide6.QtWidgets import QApplication
from signalflowgrapher.containers import MainWindows
from PySide6 import QtCore
from signalflowgrapher.utils.icon import set_app_icon
import logging
import logging.config
import argparse
from os import path


def run(argv):
    # Init logger
    logger = logging.getLogger(__name__)
    logging.config.fileConfig('signalflowgrapher/resources/logging.conf',
                              disable_existing_loggers=False)
    logger.info("Starting application")

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, help='Optional language name')
    parser.add_argument(
        'input_file',
        nargs='?',
        type=str,
        help='Optional path to a .sfg or .json file to open at startup'
    )
    args = parser.parse_args()

    app = QApplication([])

    # Set application icon early so window/taskbar show correct icon
    try:
        set_app_icon(app)
    except Exception:
        pass

    # Set language by command line argument
    if (args.language):
        language_file = "signalflowgrapher/resources/translations/%s.qm" \
                        % (args.language)
        if (path.exists(language_file)):
            logger.debug("Using translation file: %s", language_file)
            translator = QtCore.QTranslator()
            translator.load(language_file)
            app.installTranslator(translator)
        else:
            print("Language file %s not found" % language_file)
            exit(2)

    window = MainWindows.main_window()

    # Open file specified on command line / startup. If this file cannot be
    # opened (unknown file type, file not found, etc.), the application will
    # start empty, but a warning will be logged.
    if args.input_file:
        input_file = args.input_file
        file_ext = path.splitext(input_file)[1].lower()

        if file_ext not in ('.sfg', '.json'):
            logger.warning("Unsupported startup file type: %s", input_file)
        elif not path.exists(input_file):
            logger.warning("Startup file not found: %s", input_file)
        else:
            logger.info("Opening file: %s", input_file)
            window.load_file(input_file)

    window.show()
    app.exec()
