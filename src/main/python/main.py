from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QApplication
from signalflowgrapher.containers import MainWindows
from PyQt5 import QtCore
import PyQt5
import logging
import logging.config
import argparse
from os import path
import sys

if __name__ == '__main__':
    
    # Init logger
    logger = logging.getLogger(__name__)
    logging.config.fileConfig('src/main/python/signalflowgrapher/resources/logging.conf',
                              disable_existing_loggers=False)
    logger.info("Starting application")

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, help='Optional language name')
    args = parser.parse_args()

    # Configure PyQt and initialise application
    PyQt5.QtWidgets.QApplication.setAttribute(
        QtCore.Qt.AA_EnableHighDpiScaling,
        True)
    PyQt5.QtWidgets.QApplication.setAttribute(
        QtCore.Qt.AA_UseHighDpiPixmaps,
        True)
    
    # Instantiate ApplicationContext
    appctxt = ApplicationContext()
    print(appctxt.get_resource('test.txt'))
    app = QApplication([])

    # Set language by command line argument
    if (args.language):
        language_file = "src/main/python/signalflowgrapher/resources/translations/%s.qm" \
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
    window.show()

    # Invoke appctxt.app.exec()
    exit_code = appctxt.app.exec()       
    sys.exit(exit_code)