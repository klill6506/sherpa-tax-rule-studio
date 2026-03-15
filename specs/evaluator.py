"""Safe expression evaluator for tax rule formulas.

Uses Python's ast module to parse and evaluate expressions without eval().
Supports: arithmetic, comparisons, conditionals, min/max/abs/round, fact references.
"""
import ast
import operator
from decimal import Decimal, InvalidOperation

SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

SAFE_CMPOPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

SAFE_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

SAFE_FUNCTIONS = {
    "max": max,
    "min": min,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
}


class EvalError(Exception):
    """Raised when an expression cannot be evaluated."""


class SafeEvaluator:
    """Evaluate an expression string against a context of named values."""

    def __init__(self, context: dict):
        self.context = {k: self._to_number(v) for k, v in context.items()}

    @staticmethod
    def _to_number(v):
        """Convert string-encoded numbers to actual numbers."""
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                pass
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
        if isinstance(v, Decimal):
            return float(v)
        return v

    def evaluate(self, expression: str):
        """Parse and evaluate an expression string. Returns the computed value."""
        if not expression or not expression.strip():
            raise EvalError("Empty expression")

        # Normalize if/then/else to Python ternary for ast parsing
        expr = self._normalize_conditionals(expression.strip())

        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as e:
            raise EvalError(f"Syntax error: {e}") from e

        try:
            return self._eval_node(tree.body)
        except EvalError:
            raise
        except Exception as e:
            raise EvalError(f"Evaluation error: {e}") from e

    @staticmethod
    def _normalize_conditionals(expr: str) -> str:
        """Convert 'if COND then A else B' to Python 'A if COND else B'."""
        import re
        pattern = r'\bif\s+(.+?)\s+then\s+(.+?)\s+else\s+(.+)'
        match = re.match(pattern, expr, re.IGNORECASE)
        if match:
            cond, true_val, false_val = match.groups()
            return f"({true_val}) if ({cond}) else ({false_val})"
        return expr

    def _eval_node(self, node):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        # Literals
        if isinstance(node, ast.Constant):
            return node.value

        # Name lookup (fact references)
        if isinstance(node, ast.Name):
            name = node.id
            # Boolean constants
            if name == "True":
                return True
            if name == "False":
                return False
            if name == "None":
                return None
            if name in self.context:
                return self.context[name]
            # Suggest similar keys
            similar = [k for k in self.context if k.startswith(name[:3]) or name in k]
            hint = f" (did you mean {similar[0]!r}?)" if similar else ""
            raise EvalError(f"Unknown fact key {name!r}{hint}")

        # Binary operations
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_func = SAFE_BINOPS.get(type(node.op))
            if op_func is None:
                raise EvalError(f"Unsupported operator: {type(node.op).__name__}")
            return op_func(left, right)

        # Unary operations
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_func = SAFE_UNARYOPS.get(type(node.op))
            if op_func is None:
                raise EvalError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_func(operand)

        # Comparisons
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_func = SAFE_CMPOPS.get(type(op))
                if op_func is None:
                    raise EvalError(f"Unsupported comparison: {type(op).__name__}")
                if not op_func(left, right):
                    return False
                left = right
            return True

        # Boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = True
                for val in node.values:
                    result = self._eval_node(val)
                    if not result:
                        return result
                return result
            if isinstance(node.op, ast.Or):
                result = False
                for val in node.values:
                    result = self._eval_node(val)
                    if result:
                        return result
                return result

        # Ternary (if-else expression)
        if isinstance(node, ast.IfExp):
            condition = self._eval_node(node.test)
            if condition:
                return self._eval_node(node.body)
            return self._eval_node(node.orelse)

        # Function calls (max, min, abs, round)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise EvalError("Only simple function calls are supported")
            func_name = node.func.id
            if func_name not in SAFE_FUNCTIONS:
                raise EvalError(f"Unknown function: {func_name}")
            args = [self._eval_node(arg) for arg in node.args]
            return SAFE_FUNCTIONS[func_name](*args)

        raise EvalError(f"Unsupported expression type: {type(node).__name__}")


def run_rules(rules: list[dict], inputs: dict) -> dict:
    """Execute a list of rules in precedence order against given inputs.

    Returns a dict of all computed values (inputs + rule outputs).
    """
    context = dict(inputs)
    errors = []

    # Sort by precedence
    sorted_rules = sorted(rules, key=lambda r: r.get("precedence", 0))

    evaluator = SafeEvaluator(context)

    for rule in sorted_rules:
        formula = rule.get("formula", "").strip()
        if not formula:
            continue

        rule_id = rule.get("rule_id", "?")
        outputs = rule.get("outputs", [])

        # Check conditions (if any)
        conditions = rule.get("conditions", {})
        if conditions:
            # Simple condition: {"when": "expression"}
            cond_expr = conditions.get("when", "")
            if cond_expr:
                try:
                    evaluator.context = context.copy()
                    if not evaluator.evaluate(cond_expr):
                        continue  # Skip this rule — condition not met
                except EvalError:
                    continue  # If condition can't evaluate, skip

        try:
            evaluator.context = context.copy()
            result = evaluator.evaluate(formula)
        except EvalError as e:
            errors.append({"rule_id": rule_id, "error": str(e)})
            continue

        # Assign result to outputs
        if outputs:
            for output_key in outputs:
                context[output_key] = result
        else:
            # If no outputs defined, store under the rule_id
            context[f"_rule_{rule_id}"] = result

    return {"values": context, "errors": errors}
