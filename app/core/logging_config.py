"""日志配置工具。"""

from __future__ import annotations

import logging
from logging import Logger


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """初始化全局日志配置。

    M0 阶段使用最小配置，后续可以扩展到文件日志或结构化日志。
    """
    logging.basicConfig(level=level, format=DEFAULT_LOG_FORMAT)


def get_logger(name: str) -> Logger:
    """返回统一风格的 logger。"""
    return logging.getLogger(name)
