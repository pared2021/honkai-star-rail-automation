"""核心类型包..

定义核心模块的数据类型。
"""

from typing import Callable, Any, Union

# 等待条件类型定义
WaitCondition = Callable[[], Union[bool, Any]]
