# Repository Guidelines

## 项目结构与模块组织
本仓库是管理 SFT 过程中常用的工具集。

- `docs/需求文档/`：需求说明与流程设计文档。
- `docs/开发文档/`：逐步开发文档。
- `tests/`：自动化测试目录。

## 构建、测试与开发命令
当前未提供统一构建脚本，使用本地 Python 虚拟环境开发。

- `python3 -m venv .venv && source .venv/bin/activate`：创建并激活虚拟环境。
- `pip install -U pip`：升级 `pip`。
- `pytest -q`：运行测试（补充测试后执行）。
- 在 Windows 平台文档内容读取时会出现编码异常，使用 UTF-8 进行读取。
如新增依赖，请在仓库根目录维护 `requirements.txt`。

## 编码风格与命名规范
新脚本默认遵循 Python 社区规范，遵循《Code Complete 2》最佳实践，保证约 30% 的注释覆盖率。

- 缩进使用 4 个空格，文件编码为 UTF-8。
- 文件名、函数名、变量名使用 `snake_case`。
- 类名使用 `PascalCase`。
- 单个模块保持职责单一，避免“超大脚本”。

数据清洗、转换、校验逻辑建议拆分为可组合的小函数。

## 测试规范
推荐使用 `pytest`，使用 Given / When / Then（BDD 风格）写测试，在每个测试函数中使用注释描述用例。

- 测试文件放在 `tests/`。
- 文件命名：`test_<module>.py`。
- 用例命名：`test_<behavior>`。
- 至少覆盖主流程与关键边界（空行、缺列、非法标签等），保证测试覆盖率大于 70%。

## 提交与合并请求规范
提交信息沿用仓库已有 Conventional Commits 风格：

- `feat: ...`

Pull Request 建议包含：

- 变更摘要与背景；
- 影响目录；
- 数据或处理逻辑变更的输入/输出示例；
- 关联需求或 issue（如有）。