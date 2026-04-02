"""CLI 计算器引擎测试。"""

from __future__ import annotations

import pytest

from app.tools.cli_calculator.engine import CalculatorContext, CalculatorError, execute_command


def test_execute_expression_and_assignment() -> None:
    # Given: 一个空上下文
    context = CalculatorContext()

    # When: 定义变量并计算表达式
    out1 = execute_command("a = 10", context)
    out2 = execute_command("b = 20", context)
    out3 = execute_command("a * b + 5", context)

    # Then: 输出符合预期
    assert out1 == "a = 10"
    assert out2 == "b = 20"
    assert out3 == "205"


def test_execute_builtin_functions_without_trigonometric() -> None:
    # Given: 一个空上下文
    context = CalculatorContext()

    # When: 调用支持函数
    out_log = execute_command("log(100, 10)", context)
    out_sqrt = execute_command("sqrt(16)", context)

    # Then: 结果正确
    assert out_log == "2"
    assert out_sqrt == "4"

    # When / Then: 三角函数不再支持
    with pytest.raises(CalculatorError):
        execute_command("sin(1)", context)


def test_execute_should_fail_on_invalid_operation() -> None:
    # Given: 一个空上下文
    context = CalculatorContext()

    # When / Then: 非法场景报错
    with pytest.raises(CalculatorError):
        execute_command("", context)

    with pytest.raises(CalculatorError):
        execute_command("1 / 0", context)

    with pytest.raises(CalculatorError):
        execute_command("unknown + 1", context)
