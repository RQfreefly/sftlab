# SFT 工具集（sftlab）

本项目是一个基于 `Python + PySide6` 的本地桌面工具集，用于集中管理 SFT/LLM 日常高频操作，减少在多个网页工具之间切换的成本。

## 功能概览

当前应用包含以下工具模块：

1. 参数管理：保存/编辑 SFT CLI 参数模板，支持版本记录与基础校验。
2. Prompt 管理：目录分类、Prompt CRUD、历史版本管理。
3. Token 统计：支持 `gpt`、`qwen`、`llama` 三类模型计数。
4. JSON 工具：解析、格式化、压缩、转义/反转义与错误提示。
5. Diff 工具：文本行级/字符级对比，支持 JSON/Prompt 归一化比较。
6. Calculator：表达式计算、变量与历史记录。
7. Timer：分段计时与历史会话记录。
8. LLM API 测试：OpenAI 兼容接口请求与流式响应解析。

## 技术栈

- Python 3.10+
- PySide6（桌面 UI）
- SQLite（本地持久化）
- pytest（自动化测试）

## 快速开始

### 1) 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2) 启动应用

```bash
python -m app.main
```

### 3) 运行测试

```bash
pytest -q
```

## 目录结构

```text
sftlab/
├── app/
│   ├── core/            # 公共能力（日志、异常、路径等）
│   ├── storage/         # SQLite 与 Repository
│   ├── tools/           # 各工具模块实现
│   └── ui/              # 主窗口与界面装配
├── docs/
│   ├── 需求文档/
│   └── 开发文档/
├── tests/               # pytest 测试
└── requirements.txt
```

## 数据存储说明

- 数据库类型：SQLite
- 自动迁移：应用启动时自动执行 schema 迁移
- 默认路径：
  - macOS/Linux：`~/Library/Application Support/sftlab/sftlab.db`
  - Windows：`%APPDATA%/sftlab/sftlab.db`
