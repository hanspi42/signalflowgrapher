from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
from PyQt5.Qt import QCoreApplication, QDockWidget, QFileDialog, QMessageBox
from signalflowgrapher.controllers.main_controller import MainController
from signalflowgrapher.controllers.io_controller import IOController
from signalflowgrapher.gui.conditional_actions.conditional_action import \
    ConditionalAction
from signalflowgrapher.gui.conditional_actions.selection_condition import \
    MinNumNodesOrBranchesSelected
from PyQt5.QtCore import Qt
from PyQt5 import uic
import ntpath
import logging
from PyQt5 import QtCore
import PyQt5
logger = logging.getLogger(__name__)

# Configure PyQt and initialise application
PyQt5.QtWidgets.QApplication.setAttribute(
    QtCore.Qt.AA_EnableHighDpiScaling,
    True)
PyQt5.QtWidgets.QApplication.setAttribute(
    QtCore.Qt.AA_UseHighDpiPixmaps,
    True)
creator_file = ApplicationContext().get_resource("main_window.ui")
main_window_ui, x = uic.loadUiType(creator_file)

class MainWindow(QMainWindow, main_window_ui):
    def __init__(self,
                 graph_field,
                 side_widget,
                 main_controller: MainController,
                 io_controller: IOController,
                 command_handler,
                 *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.__command_handler = command_handler
        self.__graph_field = graph_field
        self.__main_controller = main_controller
        self.__io_controller = io_controller
        self.__file_path = ""
        self.setCentralWidget(graph_field)
        self.__conditional_actions = []

        dock = QDockWidget(QCoreApplication.translate("main_window",
                                                      "Operations"), self)
        dock.setWidget(side_widget)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Observe can_undo and can_redo on command handler
        # to enable/disable und and redo buttons
        self.__command_handler.can_undo.observe(
            lambda old, new: self.action_undo.setDisabled(not new))
        self.__command_handler.can_redo.observe(
            lambda old, new: self.action_redo.setDisabled(not new))

        # Observe selection changes
        self.__graph_field.selection.observe(
            self.__handle_selection_change)

        # Connect triggers to methods
        self.action_redo.triggered.connect(self.__command_handler.redo)
        self.action_undo.triggered.connect(self.__command_handler.undo)
        self.action_save.triggered.connect(self.__save)
        self.action_save_as.triggered.connect(self.__save_as)
        self.action_select_all.triggered.connect(self.__select_all)
        self.action_open.triggered.connect(self.__open)
        self.action_new.triggered.connect(self.__new)
        self.action_exit.triggered.connect(lambda: self.close())
        self.action_about.triggered.connect(self.__about)

        self.__conditional_actions.append(ConditionalAction(
            [MinNumNodesOrBranchesSelected(1)],
            self.action_remove_branch_or_node,
            self.action_remove_branch_or_node.triggered,
            lambda sel, *args:
            self.__main_controller.remove_nodes_and_branches(sel)
        ))

        # Creat inital graph
        self.__new()

    def keyPressEvent(self, event):
        # Pass ctrl key press event to graph field
        if event.key() == Qt.Key_Control:
            self.__graph_field.on_ctrl_press()

        if event.key() == Qt.Key_Escape:
            self.__graph_field.on_esc_press()

    def keyReleaseEvent(self, event):
        # Pass ctrl key release event to graph field
        if event.key() == Qt.Key_Control:
            self.__graph_field.on_ctrl_release()

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.ActivationChange:
            # Manually execute release events if window loses isActive
            if not self.isActiveWindow() and self.__graph_field:
                logger.debug("MainWindows lost isActive")
                self.__graph_field.on_ctrl_release()

    def __new(self):
        if (not self.__ask_for_continue_if_unsaved_changes()):
            return

        self.__io_controller.new_graph()
        self.__file_path = ""
        self.__set_title()

    def __save(self):
        if (not self.__file_path):
            self.__save_as()
        else:
            try:
                self.__io_controller.save_graph(self.__file_path)
            except Exception:
                logger.exception("Exception while saving to path: %s",
                                 self.__file_path)
                self.__show_error(
                    QCoreApplication.translate("main_window",
                                               "Error while saving file."
                                               " See log for details"))

    def __save_as(self):
        dialog = QFileDialog()
        dialog.setDefaultSuffix(".json")

        result = dialog.getSaveFileName(
            self,
            QCoreApplication.translate("main_window",
                                       "Save Signal-flow Graph"),
            filter="JSON (*.json)")

        if result[0]:
            try:
                self.__io_controller.save_graph(result[0])
                self.__file_path = result[0]
                self.__set_title()
            except Exception:
                logger.exception("Exception while saving to path: %s",
                                 self.__file_path)
                self.__show_error(
                    QCoreApplication.translate("main_window",
                                               "Error while saving file."
                                               " See log for details"))

    def __select_all(self):
        # Trigger select all on graph field
        self.__graph_field.select_all()

    def __open(self):
        if (not self.__ask_for_continue_if_unsaved_changes()):
            return

        dialog = QFileDialog()
        dialog.setDefaultSuffix(".json")

        result = dialog.getOpenFileName(
            self,
            QCoreApplication.translate("main_window",
                                       "Open Signal-flow Graph"),
            filter="JSON (*.json)")

        if result[0]:
            self.__file_path = result[0]
            try:
                self.__io_controller.load_graph(result[0])
                self.__set_title()
            except Exception:
                logger.exception("Exception while loading file")
                self.__show_error(
                    QCoreApplication.translate("main_window",
                                               "Error while opening file."
                                               " See log for details"))

    def closeEvent(self, event):
        if (self.__ask_for_continue_if_unsaved_changes()):
            event.accept()
        else:
            event.ignore()

    def __ask_for_continue_if_unsaved_changes(self):
        if not self.__command_handler.can_undo.get():
            # Continue if there are no unsaved changes
            return True
        else:
            # Ask if there are unsaved changes
            box = QMessageBox()
            box.addButton(QCoreApplication.translate("main_window", "Yes"),
                          box.YesRole)
            no_button = box.addButton(QCoreApplication.translate("main_window",
                                                                 "No"),
                                      box.NoRole)
            box.setDefaultButton(no_button)
            box.setWindowTitle(QCoreApplication.translate("main_window",
                                                          "Unsaved changes"))
            box.setText(QCoreApplication.translate(
                "main_window",
                "Do you really want to continue "
                "without saving changes?"))
            box.setIcon(box.Icon.Question)
            response = box.exec()

            if (response == 1):
                # Do not continue because user wants to stop
                return False
            else:
                return True

    def __set_title(self):
        # Set window title
        if (self.__file_path):
            self.setWindowTitle(ntpath.basename(self.__file_path)
                                + " - SignalFlowGrapher")
        else:
            self.setWindowTitle(
                QCoreApplication.translate("main_window",
                                           "*Unknown - SignalFlowGrapher"))

    def __show_error(self, message: str):
        box = QMessageBox()
        box.critical(self, "Error", message)

    def __handle_selection_change(self, old_selection, new_selection):
        logger.debug(
            "Selection change in graph field detected by main window")
        for action in self.__conditional_actions:
            action.update_selection(new_selection)

    def __handle_model_change(self, event):
        logger.debug(
            "Model change in graph field detected by main window")
        for action in self.__conditional_actions:
            action.handle_model_change(event)

    def __about(self):
        # Create and set about text
        box = QMessageBox()
        box.setWindowTitle("About")
        box.setText("<h1>About</h1>Initially Developed at the University"
                    " of Applied Sciences and Arts Northwestern"
                    " Switzerland (FHNW) by Nicolai Wassermann"
                    " and Simon Näf, supervised by "
                    " Prof. Dr. Hanspeter Schmid and Prof. Dr. Dominik Gruntz"
                    " <br><br> Maintained by Hanspeter Schmid."
                    " Manual: https://github.com/hanspi42/signalflowgrapher/blob/dev/MANUAL.md")
        box.exec()
