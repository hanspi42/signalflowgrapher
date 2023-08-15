from signalflowgrapher.gui.conditional_actions.selection_condition import (
    SelectionCondition)
from typing import List, Callable, Any
from PyQt5.Qt import QLineEdit, QWidget, QPushButton
from PyQt5.QtCore import pyqtSignal


class ConditionalAction(object):
    """
    Action that uses selection conditions to enable or disable the controls.
    """

    def __init__(self,
                 conditions: List[SelectionCondition],
                 control: QWidget,
                 signal: pyqtSignal,
                 action: Callable,
                 activate_action: Callable = None,
                 deactivate_action: Callable = None,
                 model_change_handler: Callable = None):
        self.__conditions = conditions
        self.__control = control
        self.__action = action
        self.__activate_action = activate_action
        self.__deactivate_action = deactivate_action
        self.__model_change_handler = model_change_handler
        signal.connect(lambda *args: action(self._selection, *args))
        self.update_selection([])

    def is_fulfilled(self) -> bool:
        return all(condition.is_fulfilled() for condition in self.__conditions)

    def update_selection(self, selection):
        self._selection = selection
        for condition in self.__conditions:
            condition.update_selection(selection)

        self.__check_conditions()

    def handle_model_change(self, event):
        if self.__model_change_handler is not None:
            self.__model_change_handler(self._selection, event)

        self.__check_conditions()

    def __check_conditions(self):
        self.__control.setEnabled(self.is_fulfilled())
        if self.is_fulfilled() and self.__activate_action is not None:
            self.__activate_action(self._selection)
        elif not self.is_fulfilled() and self.__deactivate_action is not None:
            self.__deactivate_action()


class ConditionalQPushButton(ConditionalAction):
    """
    Button control that uses selection conditions
    to enable or disable itself.
    """

    def __init__(self,
                 conditions: List[SelectionCondition],
                 control: QPushButton,
                 action: Callable,
                 activate_action: Callable = None,
                 deactivate_action: Callable = None,
                 model_change_handler: Callable = None
                 ):
        signal = control.clicked
        super().__init__(conditions,
                         control,
                         signal,
                         action,
                         activate_action,
                         deactivate_action,
                         model_change_handler)


class ConditionalQLineEdit(ConditionalAction):
    """
    Edit control that uses selection conditions
    to enable or disable itself.
    """

    def __init__(self,
                 conditions: List[SelectionCondition],
                 control: QLineEdit,
                 action: Callable[[str], Any],
                 activate_action: Callable = None,
                 model_change_handler: Callable = None):
        signal = control.textEdited
        deactivate_action = (lambda: control.setText(""))

        def activate_with_focus(sel):
            control.setFocus()
            activate_action(sel)
        super().__init__(conditions,
                         control,
                         signal,
                         action,
                         activate_with_focus,
                         deactivate_action,
                         model_change_handler)
