from importlib import resources
import logging

from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QInputDialog,
)
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QValidator, QKeyEvent
from PySide6 import QtCore, QtUiTools

from signalflowgrapher.gui.sympy_expression_validator import (
    SympyExpressionValidator)
from signalflowgrapher.gui.mason_window import MasonWindow
from signalflowgrapher.gui.graph_field import GraphField
from signalflowgrapher.model.model import (
    Model, CurvedBranch, LabelChangedTextEvent, PositionedNode)
from signalflowgrapher.controllers.main_controller import MainController
from signalflowgrapher.controllers.operation_controller import (
    OperationController)
from signalflowgrapher.controllers.io_controller import IOController
from signalflowgrapher.gui.conditional_actions.selection_condition import (
    SpecificNumBranchesSelected, SpecificNumNodesSelected,
    MaxNumNodesSelected, SubsequentBranchesSelected,
    MinNumNodesOrBranchesSelected, TwoParallelBranchesSelected,
    BranchIsSelfLoop, MinNumNodesSelected, PathHasIndependentStartVar,
    AllNodesScalable, SelectedBranchesWeighted, BranchesNextToNodesWeighted,
    NeighbourBranchesWeighted, NodesHaveNoSelfLoops,
    AllBranchesWeighted, MiddleNodeHasNumBranches)
from signalflowgrapher.gui.conditional_actions.conditional_action import (
    ConditionalQLineEdit, ConditionalQPushButton)
from signalflowgrapher.gui.ui.ui_side_widget import Ui_Form as Ui_SideWidget

logger = logging.getLogger(__name__)



class SideWidget(QWidget):
    def __init__(self, graph_field: GraphField,
                 main_controller: MainController,
                 operation_controller: OperationController,
                 io_controller: IOController,
                 model: Model):
        super(SideWidget, self).__init__()

        # Load UI from generated Python class
        self._ui = Ui_SideWidget()
        self._ui.setupUi(self)

        self.__graph_field = graph_field
        self.__main_controller = main_controller
        self.__operation_controller = operation_controller
        self.__io_controller = io_controller
        self.__model = model
        self.__graph_field.selection.observe(
            self.__handle_selection_change)
        self.__model.observe(self.__handle_model_change)

        self.__conditional_actions = []

        # Setup validators
        node_name_validator = SympyExpressionValidator()
        branch_weight_validator = SympyExpressionValidator()
        self._ui.node_name.setValidator(node_name_validator)
        self._ui.branch_weight.setValidator(branch_weight_validator)

        # Set method for validation indication with color
        node_name_validator.validationChanged.connect(
            lambda state:
            self.__set_text_edit_color(state, self._ui.node_name))
        branch_weight_validator.validationChanged.connect(
            lambda state:
            self.__set_text_edit_color(state, self._ui.branch_weight))

        def label_event_handler(sel, event):
            if (
                    isinstance(event, LabelChangedTextEvent) and
                    len(sel) > 0 and sel[0] is event.labeled_obj):
                # Set value and cursor
                if isinstance(event.labeled_obj, PositionedNode):
                    pos = self._ui.node_name.cursorPosition()
                    self._ui.node_name.setText(event.new_text)
                    self._ui.node_name.setCursorPosition(pos)
                elif isinstance(event.labeled_obj, CurvedBranch):
                    pos = self._ui.branch_weight.cursorPosition()
                    self._ui.branch_weight.setText(event.new_text)
                    self._ui.branch_weight.setCursorPosition(pos)

        self.__conditional_actions.append(ConditionalQLineEdit(
            [SpecificNumNodesSelected(1)],
            self._ui.node_name,
            lambda sel, text:
            self.__main_controller.set_node_name(sel[0], text),
            lambda sel: self._ui.node_name.setText(sel[0].name),
            label_event_handler))

        self._ui.node_name.installEventFilter(self)

        self.__conditional_actions.append(ConditionalQPushButton(
            [MinNumNodesOrBranchesSelected(1)],
            self._ui.btn_remove_nodes_and_branches,
            lambda sel, *args:
                self.__main_controller.remove_nodes_and_branches(sel)
        ))

        self.__conditional_actions.append(ConditionalQPushButton(
            [MinNumNodesSelected(1), MaxNumNodesSelected(2)],
            self._ui.btn_insert_branch,
            lambda sel, *args: (
                self.__main_controller.create_branch_auto_pos(sel[0], sel[1])
                if len(sel) == 2 else
                self.__main_controller.create_self_loop(sel[0]))
        ))

        self.__conditional_actions.append(ConditionalQLineEdit(
            [SpecificNumBranchesSelected(1)],
            self._ui.branch_weight,
            lambda sel, text:
                self.__main_controller.set_branch_weight(sel[0], text),
            lambda sel:
                self._ui.branch_weight.setText(sel[0].weight),
            label_event_handler
        ))

        self._ui.branch_weight.installEventFilter(self)

        self.__conditional_actions.append(ConditionalQPushButton(
            [SpecificNumNodesSelected(2),
             AllBranchesWeighted()],
            self._ui.btn_generate_mason,
            self.__show_mason
        ))

        # Save TikZ
        def save_tikz(sel, *args):
            dialog = QFileDialog()
            dialog.setDefaultSuffix(".tex")
            result = dialog.getSaveFileName(
                self,
                QCoreApplication.translate("side_widget", "Save TikZ Output"),
                filter="LaTex (*.tex)")
            if result[0]:
                try:
                    self.__io_controller.generate_tikz(result[0])
                except Exception:
                    logger.exception("Exception while saving tikz")
                    box = QMessageBox()
                    box.critical(
                        self,
                        QCoreApplication.translate("side_widget", "Error"),
                        QCoreApplication.translate("side_widget",
                                                   "Error while writing "
                                                   "tikz file. "
                                                   "See log for details."))

        self.__conditional_actions.append(ConditionalQPushButton(
            [],
            self._ui.btn_generate_tikz,
            save_tikz
        ))

        # Graph operations
        self.__conditional_actions.append(ConditionalQPushButton(
            [SpecificNumBranchesSelected(2),
             SubsequentBranchesSelected(),
             MiddleNodeHasNumBranches(2),
             SelectedBranchesWeighted()],
            self._ui.btn_chaining_rule,
            lambda sel, *args:
                self.safe_execute(self.__operation_controller.chain_branches, sel[0], sel[1])
        ))

        self.__conditional_actions.append(ConditionalQPushButton(
            [TwoParallelBranchesSelected(),
             SelectedBranchesWeighted()],
            self._ui.btn_combine_parallel,
            lambda sel, *args:
                self.safe_execute(self.__operation_controller.combine_parallel, sel[0], sel[1])
        ))

        self.__conditional_actions.append(ConditionalQPushButton(
            [],
            self._ui.btn_graph_transposition,
            lambda sel, *args:
                self.__operation_controller.transpose()
        ))

        self.__conditional_actions.append(ConditionalQPushButton(
            [SpecificNumNodesSelected(1),
             NodesHaveNoSelfLoops(),
             BranchesNextToNodesWeighted()],
            self._ui.btn_eliminate_node,
            lambda sel, *args:
                self.safe_execute(self.__operation_controller.eliminate_node, sel[0])
        ))

        self.__conditional_actions.append(ConditionalQPushButton(
            [SpecificNumBranchesSelected(1),
             SelectedBranchesWeighted(),
             BranchIsSelfLoop()],
            self._ui.btn_eliminate_self_loop,
            lambda sel, *args:
                self.safe_execute(self.__operation_controller.eliminate_self_loop, sel[0])
        ))

        self.__conditional_actions.append(ConditionalQPushButton(
            [SpecificNumBranchesSelected(1),
             PathHasIndependentStartVar(),
             SubsequentBranchesSelected(),
             NeighbourBranchesWeighted(),
             SelectedBranchesWeighted()],
            self._ui.btn_invert_path,
            lambda sel, *args:
                self.safe_execute(self.__operation_controller.invert_path, sel)
        ))

        def scale_path(sel, *args):
            dialog = QInputDialog()
            text, ok = dialog.getText(
                self,
                QCoreApplication.translate("side_widget", "Scale factor"),
                QCoreApplication.translate("side_widget", "Scale factor"))
            if (ok):
                self.safe_execute(self.__operation_controller.scale_path, sel, text)

        self.__conditional_actions.append(ConditionalQPushButton(
            [MinNumNodesSelected(1), AllNodesScalable(),
             BranchesNextToNodesWeighted()],
            self._ui.btn_scale_path,
            scale_path
        ))

    # Helper method to catch exceptions and show error messages
    def safe_execute(self, func, *args):
        try:
            func(*args)
        except ValueError as e:  # SymPy parse errors
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Invalid SymPy expression")
            msg.setText(str(e))
            msg.exec_()
        except Exception as e:  # Other unexpected errors
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"An unexpected error occurred:\n{str(e)}")
            msg.exec_()

    def eventFilter(self, target, event):
        # Stop processing of event if Ctrl + Z or
        # Ctrl + Y is pressed to allow undo / reod
        # when textbox is selected
        if (isinstance(event, QKeyEvent)):
            if ((event.modifiers() == Qt.KeyboardModifier.ControlModifier)
                and ((event.key() == Qt.Key.Key_Z)
                     or (event.key() == Qt.Key.Key_Y))):
                return True

        return super().eventFilter(target, event)

    def __set_text_edit_color(self, state, sender: QLineEdit):
        if state == QValidator.Acceptable:
            color = '#c4df9b'  # green
        else:
            color = QtCore.Qt.BackgroundRole

        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def __show_mason(self, sel, text):
        # Generate mason result and catch illegal sympy expressions in branchweights
        try:
            mason_result = self.__io_controller.generate_mason(
                self.__model.graph,
                sel[0],
                sel[1]
            )

        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Invalid SymPy expression")
            msg.setText(str(e))
            msg.exec_()
            return

        # Pass content and open window
        window = MasonWindow()
        window.set_content(mason_result)
        window.exec()  # Wait until window is closed

    def __handle_selection_change(self, old_selection, new_selection):
        for action in self.__conditional_actions:
            action.update_selection(new_selection)

    def __handle_model_change(self, event):
        node_pos = self._ui.node_name.cursorPosition()
        branch_weight_pos = self._ui.branch_weight.cursorPosition()
        for action in self.__conditional_actions:
            action.handle_model_change(event)
        self._ui.node_name.setCursorPosition(node_pos)
        self._ui.branch_weight.setCursorPosition(branch_weight_pos)
