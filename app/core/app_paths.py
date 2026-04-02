"""应用路径工具。"""

from __future__ import annotations

import os
from pathlib import Path


APP_DIR_NAME = "sftlab"


def get_app_data_dir() -> Path:
    """返回应用数据目录并确保目录存在。"""
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home()))
    else:
        root = Path.home() / "Library" / "Application Support"

    data_dir = root / APP_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """返回 SQLite 数据库路径。"""
    return get_app_data_dir() / "sftlab.db"
