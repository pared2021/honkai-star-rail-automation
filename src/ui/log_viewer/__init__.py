"""日志查看器模块

该模块提供日志查看器的MVP架构组件，包括Model、View、Presenter和组合类。
"""

from .log_viewer_model import LogViewerModel, LogFileWatcher, LogStatistics
from .log_viewer_view import LogViewerView, LogHighlighter
from .log_viewer_presenter import LogViewerPresenter
from .log_viewer_mvp import LogViewerMVP

__all__ = [
    # MVP组件
    'LogViewerModel',
    'LogViewerView', 
    'LogViewerPresenter',
    'LogViewerMVP',
    
    # 辅助类
    'LogFileWatcher',
    'LogStatistics',
    'LogHighlighter',
]