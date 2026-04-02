"""SFT CLI 文本解析与校验。"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

_ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


@dataclass(frozen=True)
class CliAnalysis:
    """CLI 文本分析结果。"""

    env_vars: list[str] = field(default_factory=list)
    param_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CliValidationResult:
    """CLI 文本校验结果。"""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    analysis: CliAnalysis = field(default_factory=CliAnalysis)


def validate_cli_template(name: str, cli_text: str) -> CliValidationResult:
    """校验参数模板名称与 CLI 文本。"""
    errors: list[str] = []
    warnings: list[str] = []

    if not name.strip():
        errors.append("模板名称不能为空")

    if not cli_text.strip():
        errors.append("CLI 内容不能为空")
        return CliValidationResult(False, errors=errors, warnings=warnings)

    try:
        analysis = analyze_cli_text(cli_text)
    except ValueError as exc:
        errors.append(f"CLI 解析失败: {exc}")
        return CliValidationResult(False, errors=errors, warnings=warnings)

    duplicate_env = _find_duplicates(analysis.env_vars)
    duplicate_flags = _find_duplicates(analysis.param_flags)

    if duplicate_env:
        errors.append(f"存在重复环境变量: {', '.join(duplicate_env)}")
    if duplicate_flags:
        errors.append(f"存在重复参数: {', '.join(duplicate_flags)}")

    if not analysis.param_flags:
        warnings.append("未检测到 -- 参数，确认是否为完整训练命令")

    return CliValidationResult(
        is_valid=not errors,
        errors=errors,
        warnings=warnings,
        analysis=analysis,
    )


def analyze_cli_text(cli_text: str) -> CliAnalysis:
    """提取环境变量和 -- 参数。"""
    normalized = cli_text.replace("\\\n", " ")

    try:
        tokens = shlex.split(normalized, posix=True)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    env_vars: list[str] = []
    param_flags: list[str] = []

    for token in tokens:
        if _ENV_RE.match(token):
            env_vars.append(token.split("=", 1)[0])
            continue

        if token.startswith("--"):
            flag = token[2:]
            if "=" in flag:
                flag = flag.split("=", 1)[0]
            if flag:
                param_flags.append(flag)

    return CliAnalysis(env_vars=env_vars, param_flags=param_flags)


def _find_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []

    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
            continue
        seen.add(value)

    return duplicates
