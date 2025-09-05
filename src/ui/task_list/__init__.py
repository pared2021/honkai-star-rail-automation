"""任务列表UI模块

该模块提供任务列表的MVP架构实现，包括：
- TaskListModel: 任务列表数据模型
- TaskListView: 任务列表视图界面
- TaskListPresenter: 任务列表业务逻辑控制器
- TaskListMVP: 任务列表MVP集成类

使用示例:
    # 创建任务列表组件
    task_list_mvp = TaskListMVP()
    
    # 获取视图组件
    widget = task_list_mvp.get_widget()
    
    # 连接信号
    task_list_mvp.task_selected.connect(on_task_selected)
    task_list_mvp.task_edit_requested.connect(on_task_edit)
    
    # 刷新任务列表
    task_list_mvp.refresh_tasks()
"""

from .task_list_model import TaskListModel
from .task_list_view import TaskListView
from .task_list_presenter import TaskListPresenter
from .task_list_mvp import TaskListMVP

__all__ = [
    'TaskListModel',
    'TaskListView', 
    'TaskListPresenter',
    'TaskListMVP'
]