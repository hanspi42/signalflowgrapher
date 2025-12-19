from PySide6.QtGui import QValidator
from PySide6.QtCore import Signal
from sympy.parsing.sympy_parser import parse_expr, TokenError
from sympy.abc import _clash


class SympyExpressionValidator(QValidator):
    validationChanged = Signal(QValidator.State)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, s: str, pos: int):
        """
        Validate SymPyExpression and emit validation changed signal.
        """
        state = QValidator.Intermediate

        try:
            if s != "":
                parse_expr(s, local_dict=_clash)
                # If no exception occurs the expression is valid
                state = QValidator.Acceptable
        except (TokenError, SyntaxError, AttributeError, TypeError):
            # Leave state on intermediate, could be an incomplete expression
            pass

        self.validationChanged.emit(state)
        return state, s, pos
