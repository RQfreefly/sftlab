"""应用级异常处理。"""

from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType
from typing import Optional, Type

LOGGER = logging.getLogger(__name__)


def install_global_exception_handler() -> None:
    """注册全局未捕获异常钩子。"""
    sys.excepthook = _handle_uncaught_exception


def _handle_uncaught_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
) -> None:
    """记录未捕获异常。

    KeyboardInterrupt 交回默认处理，避免影响中断行为。
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    LOGGER.error("Unhandled exception: %s", exc_value)
    if exc_traceback is not None:
        trace = "".join(traceback.format_tb(exc_traceback))
        LOGGER.error("Traceback:\n%s", trace)
