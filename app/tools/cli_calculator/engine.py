"""CLI 计算器核心逻辑。"""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CalculatorContext:
    """计算上下文，保存变量。"""

    variables: dict[str, float] = field(default_factory=dict)


_ALLOWED_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
}

_ALLOWED_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}


class CalculatorError(ValueError):
    """计算器业务异常。"""


def execute_command(command: str, context: CalculatorContext) -> str:
    """执行一条 CLI 命令并返回展示字符串。"""
    text = command.strip()
    if not text:
        raise CalculatorError("输入不能为空")

    tree = ast.parse(text, mode="exec")
    if len(tree.body) != 1:
        raise CalculatorError("仅支持单条表达式或赋值")

    node = tree.body[0]
    if isinstance(node, ast.Assign):
        return _execute_assign(node, context)
    if isinstance(node, ast.Expr):
        value = _eval_expr(node.value, context)
        return _format_number(value)

    raise CalculatorError("仅支持表达式和变量赋值")


def _execute_assign(node: ast.Assign, context: CalculatorContext) -> str:
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        raise CalculatorError("赋值语法仅支持 name = expr")

    name = node.targets[0].id
    if not name.isidentifier():
        raise CalculatorError("变量名非法")

    value = _eval_expr(node.value, context)
    context.variables[name] = value
    return f"{name} = {_format_number(value)}"


def _eval_expr(node: ast.AST, context: CalculatorContext) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise CalculatorError("仅支持数值常量")

    if isinstance(node, ast.Name):
        if node.id in context.variables:
            return float(context.variables[node.id])
        if node.id in _ALLOWED_CONSTANTS:
            return float(_ALLOWED_CONSTANTS[node.id])
        raise CalculatorError(f"未定义变量: {node.id}")

    if isinstance(node, ast.BinOp):
        left = _eval_expr(node.left, context)
        right = _eval_expr(node.right, context)
        return _eval_binop(node.op, left, right)

    if isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand, context)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise CalculatorError("不支持的一元运算")

    if isinstance(node, ast.Call):
        return _eval_call(node, context)

    raise CalculatorError("不支持的表达式")


def _eval_binop(op: ast.operator, left: float, right: float) -> float:
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.Div):
        if right == 0:
            raise CalculatorError("除数不能为 0")
        return left / right
    if isinstance(op, ast.Pow):
        return left**right
    if isinstance(op, ast.Mod):
        if right == 0:
            raise CalculatorError("模运算除数不能为 0")
        return left % right

    raise CalculatorError("不支持的二元运算")


def _eval_call(node: ast.Call, context: CalculatorContext) -> float:
    if not isinstance(node.func, ast.Name):
        raise CalculatorError("仅支持函数名调用")

    fn_name = node.func.id
    if fn_name not in _ALLOWED_FUNCTIONS:
        raise CalculatorError(f"不支持的函数: {fn_name}")

    if node.keywords:
        raise CalculatorError("函数调用不支持关键字参数")

    args = [_eval_expr(arg, context) for arg in node.args]
    fn = _ALLOWED_FUNCTIONS[fn_name]
    try:
        value = fn(*args)
    except Exception as exc:  # noqa: BLE001
        raise CalculatorError(f"函数执行失败: {exc}") from exc

    return float(value)


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.12g}"
