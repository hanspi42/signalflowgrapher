from PyQt5.Qt import QValidator
from PyQt5.QtCore import pyqtSignal
from sympy.parsing.sympy_parser import parse_expr, TokenError


class SympyExpressionValidator(QValidator):
    validationChanged = pyqtSignal(QValidator.State)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, s: str, pos: int):
        """
        Validate SymPyExpression and emit validation changed signal.
        """
        state = QValidator.Intermediate

        try:
            if s != "":
                parse_expr(s)
                # If no exception occurs the expression is valid
                state = QValidator.Acceptable
        except (TokenError, SyntaxError, AttributeError):
            # Leave state on intermediate, could be an incomplete expression
            pass

        self.validationChanged.emit(state)
        return state, s, pos
