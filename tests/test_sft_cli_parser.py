"""SFT CLI 解析器测试。"""

from __future__ import annotations

from app.tools.sft_params.parser import analyze_cli_text, validate_cli_template


def test_analyze_cli_text_extracts_env_and_flags() -> None:
    # Given: 包含环境变量和参数的训练命令
    cli_text = (
        "CUDA_VISIBLE_DEVICES=0,1 NPROC_PER_NODE=2 swift sft "
        "--model /ssd/model --learning_rate 1e-4 --max_length=8192"
    )

    # When: 解析 CLI
    analysis = analyze_cli_text(cli_text)

    # Then: 环境变量与参数都能提取
    assert analysis.env_vars == ["CUDA_VISIBLE_DEVICES", "NPROC_PER_NODE"]
    assert analysis.param_flags == ["model", "learning_rate", "max_length"]


def test_validate_cli_template_should_fail_on_duplicate_flags() -> None:
    # Given: 含重复参数的命令
    cli_text = "swift sft --model /a --model /b --lr 1e-4"

    # When: 进行校验
    result = validate_cli_template("demo", cli_text)

    # Then: 返回重复参数错误
    assert result.is_valid is False
    assert any("重复参数" in message for message in result.errors)


def test_validate_cli_template_should_warn_when_no_flags() -> None:
    # Given: 只有普通文本，不包含 -- 参数
    cli_text = "echo hello world"

    # When: 进行校验
    result = validate_cli_template("demo", cli_text)

    # Then: 校验通过但带有警告
    assert result.is_valid is True
    assert any("未检测到 -- 参数" in message for message in result.warnings)
