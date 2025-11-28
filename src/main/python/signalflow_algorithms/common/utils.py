from sympy.parsing.sympy_parser import parse_expr
from sympy.abc import _clash

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
        return parse_expr(weight, local_dict=_clash)
    except Exception as e:
        raise ValueError(
            f"Invalid expression '{weight}' in branch "
            f"{branch.start.name} → {branch.end.name}"
        ) from e