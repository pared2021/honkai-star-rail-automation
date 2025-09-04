# -*- coding: utf-8 -*-
"""MVP模式基础组件.

该包提供了MVP（Model-View-Presenter）模式的基础实现，
用于构建可测试、可维护的GUI应用程序。
"""

from .base_model import BaseModel
from .base_presenter import BasePresenter
from .base_view import BaseView

__all__ = ["BaseModel", "BaseView", "BasePresenter"]
