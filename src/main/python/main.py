import logging
import logging.config
import argparse
from os import path
import sys
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from signalflowgrapher.containers import MainWindows

if __name__ == '__main__':
    # Instantiate ApplicationContext
    appctxt = ApplicationContext()

    # Init logger
    logger = logging.getLogger(__name__)
    logconfig = appctxt.get_resource('logging.conf')
    logging.config.fileConfig(logconfig,
                              disable_existing_loggers=False)
    logger.info("Starting application")

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, help='Optional language name')
    args = parser.parse_args()

    app = QApplication([])

    # Set language by command line argument.  This is not done through the
    # application context yet because it anyway only works on the command line
    if (args.language):
        language_file = (
            "src/main/python/signalflowgrapher/resources/translations/%s.qm"
            % (args.language))
        if (path.exists(language_file)):
            logger.debug("Using translation file: %s", language_file)
            translator = QtCore.QTranslator()
            translator.load(language_file)
            app.installTranslator(translator)
        else:
            print("Language file %s not found" % language_file)
            exit(2)

    window = MainWindows.main_window()
    window.show()

    # Invoke appctxt.app.exec()
    exit_code = appctxt.app.exec()
    sys.exit(exit_code)

# Review comments 08/23: There was a "Configure PyQt" here that has been moved
# to # main_window.py, mainly to make it possible to get this file flake8
# clean.
