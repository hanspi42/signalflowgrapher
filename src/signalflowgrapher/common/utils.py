from sympy.parsing.sympy_parser import parse_expr
from sympy.abc import _clash
from sympy.core.expr import Expr
from sympy.core.function import AppliedUndef

# SymPy's clash list minus 'S', so S(1), S.Half, S(1)/S(3), ... mean
# SymPy's singleton registry (exact rationals) instead of a symbol named S.
CLASH = {name: value for name, value in _clash.items() if name != 'S'}

def parse_expression(expression: str,
                     allow_undefined_functions: bool = False) -> "Expr":
    try:
        expr = parse_expr(expression, local_dict=dict(CLASH))
    except Exception as e:
        raise ValueError(f"Invalid expression '{expression}'") from e

    if not isinstance(expr, Expr):
        raise ValueError(f"Invalid expression '{expression}'")

    if not allow_undefined_functions and expr.atoms(AppliedUndef):
        raise ValueError(
            f"Unsupported function call in expression '{expression}'")

    return expr

def parse_weight(weight: str, branch) -> "Expr":
    """
    Safely parse a branch weight into a SymPy expression.

    Args:
        weight: The string weight of the branch.
        branch: Branch object (used for error message).

    Returns:
        sympy.Expr: Parsed SymPy expression.

    Raises:
        ValueError: If parsing fails, with branch info included.
    """
    try:
        return parse_expression(weight)
    except Exception as e:
        raise ValueError(
            f"Invalid expression '{weight}' in branch "
            f"{branch.start.name} → {branch.end.name}"
        ) from e

def parse_factor(factor: str) -> "Expr":
    """
    Safely parse a string into a SymPy expression (for factors).

    Args:
        factor: The string to parse.

    Returns:
        sympy.Expr: Parsed SymPy expression.

    Raises:
        ValueError: If parsing fails.
    """
    try:
        return parse_expression(factor)
    except Exception as e:
        raise ValueError(f"Invalid expression '{factor}' as factor used") from e

def parse_nodename(nodename: str) -> "Expr":
    """
    Safely parse a string into a SymPy expression (for node names).

    Args:
        nodename: The string to parse.

    Returns:
        sympy.Expr: Parsed SymPy expression.

    Raises:
        ValueError: If parsing fails.
    """
    try:
        return parse_expression(nodename, allow_undefined_functions=True)
    except Exception as e:
        raise ValueError(f"Invalid expression '{nodename}' as node name used") from e