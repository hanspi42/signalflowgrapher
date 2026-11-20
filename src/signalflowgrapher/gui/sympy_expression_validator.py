from PySide6.QtGui import QValidator
from PySide6.QtCore import Signal
from signalflowgrapher.common.utils import parse_expression


class SympyExpressionValidator(QValidator):
    validationChanged = Signal(QValidator.State)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, s: str, pos: int):
        """
        Validate SymPyExpression and emit validation changed signal.
        """
        state = QValidator.Intermediate

        if s != "":
            try:
                parse_expression(s)
                # If no exception occurs the expression is valid
                state = QValidator.Acceptable
            except ValueError:
                # Leave state on intermediate, could be an incomplete
                # expression or contain unsupported constructs
                pass

        self.validationChanged.emit(state)
        return state, s, pos
