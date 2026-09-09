import ast
import operator

class CalculatorError(ValueError):
    """Raised when an expression is invalid or uses unsupported syntax."""

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
} 

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

    
def calculate(expression: str) -> int | float:
    expression = expression.strip()

    if not expression:
        raise CalculatorError("Expression cannot be empty.")

    if len(expression) > 200:
        raise CalculatorError("Expression is too long.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CalculatorError("Invalid arithmetic expression.") from error

    return _evaluate_node(tree.body)

def _evaluate_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError("Only numeric values are allowed.")
        return node.value

    if isinstance(node, ast.BinOp):
        operation = BINARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise CalculatorError("This arithmetic operation is not allowed.")

        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)

        try:
            return operation(left, right)
        except ZeroDivisionError as error:
            raise CalculatorError("Division by zero is not allowed.") from error

    if isinstance(node, ast.UnaryOp):
        operation = UNARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise CalculatorError("This unary operation is not allowed.")

        operand = _evaluate_node(node.operand)
        return operation(operand)
    
    raise CalculatorError("Only basic arithmetic is allowed.")
        
