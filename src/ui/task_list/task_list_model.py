"""任务列表数据模型模块.

定义任务列表界面的数据模型。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal, QModelIndex
from PyQt5.QtGui import QColor

from ...core.enhanced_task_executor import TaskConfig, TaskExecution, TaskStatus, TaskType, TaskPriority


class TaskListModel(QAbstractTableModel):
    """任务列表数据模型。"""
    
    # 信号定义
    taskUpdated = pyqtSignal(str)  # 任务更新信号
    taskAdded = pyqtSignal(str)    # 任务添加信号
    taskRemoved = pyqtSignal(str)  # 任务移除信号
    
    # 列定义
    COLUMNS = [
        "任务名称",
        "类型", 
        "状态",
        "优先级",
        "进度",
        "创建时间",
        "执行时间"
    ]
    
    def __init__(self, parent=None):
        """初始化任务列表模型。"""
        super().__init__(parent)
        self._tasks: List[TaskExecution] = []
        self._task_map: Dict[str, TaskExecution] = {}
        
    def rowCount(self, parent=QModelIndex()) -> int:
        """返回行数。"""
        return len(self._tasks)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """返回列数。"""
        return len(self.COLUMNS)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """返回表头数据。"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """返回单元格数据。"""
        if not index.isValid() or index.row() >= len(self._tasks):
            return None
            
        task = self._tasks[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # 任务名称
                return task.task_config.name
            elif column == 1:  # 类型
                return task.task_config.task_type.value
            elif column == 2:  # 状态
                return task.status.value
            elif column == 3:  # 优先级
                return task.task_config.priority.value
            elif column == 4:  # 进度
                return f"{task.progress:.1%}"
            elif column == 5:  # 创建时间
                return task.task_config.created_at.strftime("%Y-%m-%d %H:%M:%S")
            elif column == 6:  # 执行时间
                if task.execution_time > 0:
                    return f"{task.execution_time:.2f}s"
                return "-"
                
        elif role == Qt.BackgroundRole:
            # 根据状态设置背景色
            if task.status == TaskStatus.RUNNING:
                return QColor(144, 238, 144)  # 浅绿色
            elif task.status == TaskStatus.FAILED:
                return QColor(255, 182, 193)  # 浅红色
            elif task.status == TaskStatus.COMPLETED:
                return QColor(173, 216, 230)  # 浅蓝色
            elif task.status == TaskStatus.PAUSED:
                return QColor(255, 255, 224)  # 浅黄色
                
        elif role == Qt.UserRole:
            # 返回完整的任务执行对象
            return task
            
        return None
    
    def addTask(self, task_execution: TaskExecution) -> bool:
        """添加任务。"""
        if task_execution.task_id in self._task_map:
            return False
            
        self.beginInsertRows(QModelIndex(), len(self._tasks), len(self._tasks))
        self._tasks.append(task_execution)
        self._task_map[task_execution.task_id] = task_execution
        self.endInsertRows()
        
        self.taskAdded.emit(task_execution.task_id)
        return True
    
    def updateTask(self, task_execution: TaskExecution) -> bool:
        """更新任务。"""
        if task_execution.task_id not in self._task_map:
            return False
            
        # 找到任务在列表中的位置
        for i, task in enumerate(self._tasks):
            if task.task_id == task_execution.task_id:
                self._tasks[i] = task_execution
                self._task_map[task_execution.task_id] = task_execution
                
                # 通知视图更新
                top_left = self.index(i, 0)
                bottom_right = self.index(i, len(self.COLUMNS) - 1)
                self.dataChanged.emit(top_left, bottom_right)
                
                self.taskUpdated.emit(task_execution.task_id)
                return True
                
        return False
    
    def removeTask(self, task_id: str) -> bool:
        """移除任务。"""
        if task_id not in self._task_map:
            return False
            
        # 找到任务在列表中的位置
        for i, task in enumerate(self._tasks):
            if task.task_id == task_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                del self._tasks[i]
                del self._task_map[task_id]
                self.endRemoveRows()
                
                self.taskRemoved.emit(task_id)
                return True
                
        return False
    
    def getTask(self, task_id: str) -> Optional[TaskExecution]:
        """获取任务。"""
        return self._task_map.get(task_id)
    
    def getAllTasks(self) -> List[TaskExecution]:
        """获取所有任务。"""
        return self._tasks.copy()
    
    def clearTasks(self):
        """清空所有任务。"""
        self.beginResetModel()
        self._tasks.clear()
        self._task_map.clear()
        self.endResetModel()
    
    def getTasksByStatus(self, status: TaskStatus) -> List[TaskExecution]:
        """根据状态获取任务。"""
        return [task for task in self._tasks if task.status == status]
