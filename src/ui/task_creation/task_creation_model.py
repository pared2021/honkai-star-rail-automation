"""任务创建数据模型模块..

定义任务创建界面的数据模型。
"""

from typing import Optional, Dict, Any, List
from PyQt5.QtCore import QObject, pyqtSignal
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

from ...core.enhanced_task_executor import (
    TaskType, TaskPriority, TaskConfig, TaskStatus
)


@dataclass
class TaskTemplate:
    """任务模板数据类。"""
    name: str
    description: str = ""
    task_type: TaskType = TaskType.AUTOMATION
    priority: TaskPriority = TaskPriority.MEDIUM
    retry_count: int = 3
    timeout: int = 300
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    auto_retry: bool = True
    max_concurrent: int = 1
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。
        
        Returns:
            Dict[str, Any]: 字典数据
        """
        return {
            'name': self.name,
            'description': self.description,
            'task_type': self.task_type.value,
            'priority': self.priority.value,
            'retry_count': self.retry_count,
            'timeout': self.timeout,
            'dependencies': self.dependencies,
            'parameters': self.parameters,
            'enabled': self.enabled,
            'auto_retry': self.auto_retry,
            'max_concurrent': self.max_concurrent,
            'tags': self.tags
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskTemplate':
        """从字典创建模板。
        
        Args:
            data: 字典数据
            
        Returns:
            TaskTemplate: 任务模板对象
        """
        # 转换枚举类型
        task_type = TaskType.AUTOMATION
        for t in TaskType:
            if t.value == data.get('task_type', ''):
                task_type = t
                break
                
        priority = TaskPriority.MEDIUM
        for p in TaskPriority:
            if p.value == data.get('priority', ''):
                priority = p
                break
                
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            task_type=task_type,
            priority=priority,
            retry_count=data.get('retry_count', 3),
            timeout=data.get('timeout', 300),
            dependencies=data.get('dependencies', []),
            parameters=data.get('parameters', {}),
            enabled=data.get('enabled', True),
            auto_retry=data.get('auto_retry', True),
            max_concurrent=data.get('max_concurrent', 1),
            tags=data.get('tags', [])
        )


class TaskCreationModel(QObject):
    """任务创建数据模型。"""
    
    # 信号定义
    templateLoaded = pyqtSignal(object)  # TaskTemplate
    templateSaved = pyqtSignal(str)  # 文件路径
    taskValidated = pyqtSignal(bool, str)  # 是否有效, 错误信息
    
    def __init__(self, parent=None):
        """初始化任务创建模型。
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self.current_template = None
        self.templates_dir = "templates/tasks"
        self._ensure_templates_dir()
        
    def _ensure_templates_dir(self):
        """确保模板目录存在。"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)
            
    def create_task_config(self, form_data: Dict[str, Any]) -> Optional[TaskConfig]:
        """创建任务配置。
        
        Args:
            form_data: 表单数据
            
        Returns:
            Optional[TaskConfig]: 任务配置对象
        """
        try:
            # 验证数据
            is_valid, error_msg = self.validate_task_data(form_data)
            if not is_valid:
                self.taskValidated.emit(False, error_msg)
                return None
                
            # 转换枚举类型
            task_type = TaskType.AUTOMATION
            for t in TaskType:
                if t.value == form_data.get('task_type', ''):
                    task_type = t
                    break
                    
            priority = TaskPriority.MEDIUM
            for p in TaskPriority:
                if p.value == form_data.get('priority', ''):
                    priority = p
                    break
                    
            # 解析依赖任务
            dependencies = []
            if form_data.get('dependencies'):
                dependencies = [dep.strip() for dep in form_data['dependencies'].split(',') if dep.strip()]
                
            # 解析任务参数
            parameters = {}
            if form_data.get('parameters'):
                try:
                    if isinstance(form_data['parameters'], str):
                        parameters = json.loads(form_data['parameters'])
                    else:
                        parameters = form_data['parameters']
                except json.JSONDecodeError:
                    self.taskValidated.emit(False, "任务参数格式错误，请使用有效的JSON格式")
                    return None
                    
            # 解析标签
            tags = []
            if form_data.get('tags'):
                tags = [tag.strip() for tag in form_data['tags'].split(',') if tag.strip()]
                
            # 创建任务配置
            task_config = TaskConfig(
                task_id=form_data.get('task_id'),
                name=form_data['name'],
                description=form_data.get('description', ''),
                task_type=task_type,
                priority=priority,
                retry_count=form_data.get('retry_count', 3),
                timeout=form_data.get('timeout', 300),
                dependencies=dependencies,
                parameters=parameters,
                scheduled_time=form_data.get('scheduled_time'),
                enabled=form_data.get('enabled', True),
                auto_retry=form_data.get('auto_retry', True),
                max_concurrent=form_data.get('max_concurrent', 1),
                tags=tags
            )
            
            self.taskValidated.emit(True, "")
            return task_config
            
        except Exception as e:
            self.taskValidated.emit(False, f"创建任务配置失败: {e}")
            return None
            
    def validate_task_data(self, form_data: Dict[str, Any]) -> tuple[bool, str]:
        """验证任务数据。
        
        Args:
            form_data: 表单数据
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查必填字段
        if not form_data.get('name', '').strip():
            return False, "任务名称不能为空"
            
        # 检查任务类型
        task_type = form_data.get('task_type', '')
        valid_types = [t.value for t in TaskType]
        if task_type not in valid_types:
            return False, f"无效的任务类型: {task_type}"
            
        # 检查优先级
        priority = form_data.get('priority', '')
        valid_priorities = [p.value for p in TaskPriority]
        if priority not in valid_priorities:
            return False, f"无效的优先级: {priority}"
            
        # 检查重试次数
        retry_count = form_data.get('retry_count', 0)
        if not isinstance(retry_count, int) or retry_count < 0 or retry_count > 10:
            return False, "重试次数必须是0-10之间的整数"
            
        # 检查超时时间
        timeout = form_data.get('timeout', 0)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
            return False, "超时时间必须是1-3600秒之间的整数"
            
        # 检查最大并发数
        max_concurrent = form_data.get('max_concurrent', 1)
        if not isinstance(max_concurrent, int) or max_concurrent < 1 or max_concurrent > 10:
            return False, "最大并发数必须是1-10之间的整数"
            
        # 检查任务参数格式
        parameters = form_data.get('parameters')
        if parameters:
            try:
                if isinstance(parameters, str):
                    json.loads(parameters)
            except json.JSONDecodeError:
                return False, "任务参数格式错误，请使用有效的JSON格式"
                
        return True, ""
        
    def save_template(self, template_data: Dict[str, Any], file_path: str = None) -> bool:
        """保存任务模板。
        
        Args:
            template_data: 模板数据
            file_path: 文件路径，如果为None则自动生成
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if file_path is None:
                # 自动生成文件名
                template_name = template_data.get('name', 'template')
                safe_name = "".join(c for c in template_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(self.templates_dir, f"{safe_name}_{timestamp}.json")
                
            # 创建模板对象
            template = TaskTemplate.from_dict(template_data)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
                
            self.templateSaved.emit(file_path)
            return True
            
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False
            
    def load_template(self, file_path: str) -> bool:
        """加载任务模板。
        
        Args:
            file_path: 模板文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                
            template = TaskTemplate.from_dict(template_data)
            self.current_template = template
            self.templateLoaded.emit(template)
            return True
            
        except Exception as e:
            print(f"加载模板失败: {e}")
            return False
            
    def get_available_templates(self) -> List[str]:
        """获取可用的模板列表。
        
        Returns:
            List[str]: 模板文件路径列表
        """
        templates = []
        
        if os.path.exists(self.templates_dir):
            for file_name in os.listdir(self.templates_dir):
                if file_name.endswith('.json'):
                    templates.append(os.path.join(self.templates_dir, file_name))
                    
        return templates
        
    def get_default_template(self) -> TaskTemplate:
        """获取默认模板。
        
        Returns:
            TaskTemplate: 默认任务模板
        """
        return TaskTemplate(
            name="新任务",
            description="",
            task_type=TaskType.AUTOMATION,
            priority=TaskPriority.MEDIUM,
            retry_count=3,
            timeout=300,
            dependencies=[],
            parameters={},
            enabled=True,
            auto_retry=True,
            max_concurrent=1,
            tags=[]
        )
        
    def create_template_from_config(self, task_config: TaskConfig) -> TaskTemplate:
        """从任务配置创建模板。
        
        Args:
            task_config: 任务配置
            
        Returns:
            TaskTemplate: 任务模板
        """
        return TaskTemplate(
            name=task_config.name or "新任务",
            description=task_config.description or "",
            task_type=task_config.task_type,
            priority=task_config.priority,
            retry_count=task_config.retry_count or 3,
            timeout=task_config.timeout or 300,
            dependencies=task_config.dependencies or [],
            parameters=task_config.parameters or {},
            enabled=getattr(task_config, 'enabled', True),
            auto_retry=getattr(task_config, 'auto_retry', True),
            max_concurrent=getattr(task_config, 'max_concurrent', 1),
            tags=getattr(task_config, 'tags', [])
        )
        
    def get_task_type_options(self) -> List[tuple[str, TaskType]]:
        """获取任务类型选项。
        
        Returns:
            List[tuple[str, TaskType]]: (显示名称, 枚举值) 列表
        """
        return [(task_type.value, task_type) for task_type in TaskType]
        
    def get_priority_options(self) -> List[tuple[str, TaskPriority]]:
        """获取优先级选项。
        
        Returns:
            List[tuple[str, TaskPriority]]: (显示名称, 枚举值) 列表
        """
        return [(priority.value, priority) for priority in TaskPriority]
