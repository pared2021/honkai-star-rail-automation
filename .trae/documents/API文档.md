# 崩坏星穹铁道自动化助手 - API文档

## 目录

1. [概述](#概述)
2. [核心模块](#核心模块)
3. [接口规范](#接口规范)
4. [使用示例](#使用示例)
5. [错误处理](#错误处理)
6. [扩展开发](#扩展开发)

## 概述

本文档描述了崩坏星穹铁道自动化助手的核心API接口，包括游戏检测、自动化操作、任务管理等主要功能模块的接口定义和使用方法。

### 架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │  Service Layer  │    │   Core Layer    │
│                 │    │                 │    │                 │
│ - MainWindow    │◄──►│ - TaskManager   │◄──►│ - GameDetector  │
│ - TaskCreation  │    │ - EventBus      │    │ - GameOperator  │
│ - Settings      │    │ - ConfigManager │    │ - OCRDetector   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Data Layer     │
                       │                 │
                       │ - Database      │
                       │ - FileSystem    │
                       │ - Configuration │
                       └─────────────────┘
```

### 主要特性

- **模块化设计**: 清晰的模块分离和接口定义
- **异步支持**: 支持异步操作和事件驱动
- **类型安全**: 使用Python类型注解
- **错误处理**: 完善的异常处理机制
- **可扩展性**: 支持插件和自定义扩展

## 核心模块

### 1. 游戏检测模块 (GameDetector)

#### 类定义

```python
from typing import Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class WindowInfo:
    """游戏窗口信息"""
    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]  # (x, y, width, height)
    is_foreground: bool

@dataclass
class DetectionResult:
    """检测结果"""
    success: bool
    confidence: float
    position: Optional[Tuple[int, int]]
    template_name: str
    timestamp: float

class GameDetector:
    """游戏检测器"""
    
    def __init__(self, config: dict):
        """初始化游戏检测器
        
        Args:
            config: 配置字典，包含检测参数
        """
        pass
    
    def find_game_window(self) -> Optional[WindowInfo]:
        """查找游戏窗口
        
        Returns:
            WindowInfo: 游戏窗口信息，未找到返回None
        """
        pass
    
    def detect_template(self, template_name: str, 
                       region: Optional[Tuple[int, int, int, int]] = None) -> DetectionResult:
        """检测模板
        
        Args:
            template_name: 模板名称
            region: 检测区域 (x, y, width, height)
            
        Returns:
            DetectionResult: 检测结果
        """
        pass
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> bytes:
        """截取屏幕
        
        Args:
            region: 截图区域
            
        Returns:
            bytes: 图片数据
        """
        pass
```

#### 使用示例

```python
from src.core.game_detector import GameDetector

# 初始化检测器
config = {
    'threshold': 0.8,
    'timeout': 30,
    'template_path': 'assets/templates/'
}
detector = GameDetector(config)

# 查找游戏窗口
window = detector.find_game_window()
if window:
    print(f"找到游戏窗口: {window.title}")
    print(f"窗口位置: {window.rect}")

# 检测模板
result = detector.detect_template('main_menu')
if result.success:
    print(f"检测成功，置信度: {result.confidence}")
    print(f"位置: {result.position}")
```

### 2. 游戏操作模块 (GameOperator)

#### 类定义

```python
from enum import Enum
from typing import Union, List

class ClickType(Enum):
    """点击类型"""
    LEFT = "left"
    RIGHT = "right"
    DOUBLE = "double"

class KeyType(Enum):
    """按键类型"""
    ENTER = "enter"
    ESC = "escape"
    SPACE = "space"
    TAB = "tab"

@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    message: str
    timestamp: float
    duration: float

class GameOperator:
    """游戏操作器"""
    
    def __init__(self, detector: GameDetector):
        """初始化游戏操作器
        
        Args:
            detector: 游戏检测器实例
        """
        pass
    
    def click(self, x: int, y: int, 
             click_type: ClickType = ClickType.LEFT,
             delay: float = 0.5) -> OperationResult:
        """点击指定位置
        
        Args:
            x, y: 点击坐标
            click_type: 点击类型
            delay: 操作后延迟时间
            
        Returns:
            OperationResult: 操作结果
        """
        pass
    
    def click_template(self, template_name: str,
                      offset: Tuple[int, int] = (0, 0),
                      timeout: float = 10.0) -> OperationResult:
        """点击模板位置
        
        Args:
            template_name: 模板名称
            offset: 偏移量
            timeout: 超时时间
            
        Returns:
            OperationResult: 操作结果
        """
        pass
    
    def send_key(self, key: Union[str, KeyType], 
                delay: float = 0.5) -> OperationResult:
        """发送按键
        
        Args:
            key: 按键
            delay: 操作后延迟时间
            
        Returns:
            OperationResult: 操作结果
        """
        pass
    
    def drag(self, start: Tuple[int, int], 
            end: Tuple[int, int],
            duration: float = 1.0) -> OperationResult:
        """拖拽操作
        
        Args:
            start: 起始位置
            end: 结束位置
            duration: 拖拽持续时间
            
        Returns:
            OperationResult: 操作结果
        """
        pass
```

#### 使用示例

```python
from src.core.game_operator import GameOperator, ClickType, KeyType

# 初始化操作器
operator = GameOperator(detector)

# 点击操作
result = operator.click(100, 200, ClickType.LEFT)
if result.success:
    print("点击成功")

# 点击模板
result = operator.click_template('start_button')
if result.success:
    print("点击开始按钮成功")

# 发送按键
result = operator.send_key(KeyType.ENTER)
if result.success:
    print("发送回车键成功")

# 拖拽操作
result = operator.drag((100, 100), (200, 200), duration=2.0)
if result.success:
    print("拖拽操作成功")
```

### 3. 任务管理模块 (TaskManager)

#### 类定义

```python
from enum import Enum
from typing import Dict, List, Callable, Any
from datetime import datetime

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TaskConfig:
    """任务配置"""
    name: str
    description: str
    priority: TaskPriority
    max_retries: int
    timeout: float
    parameters: Dict[str, Any]

@dataclass
class TaskInfo:
    """任务信息"""
    id: str
    config: TaskConfig
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float
    error_message: Optional[str]

class TaskManager:
    """任务管理器"""
    
    def __init__(self, max_concurrent: int = 3):
        """初始化任务管理器
        
        Args:
            max_concurrent: 最大并发任务数
        """
        pass
    
    def create_task(self, config: TaskConfig) -> str:
        """创建任务
        
        Args:
            config: 任务配置
            
        Returns:
            str: 任务ID
        """
        pass
    
    def start_task(self, task_id: str) -> bool:
        """启动任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否启动成功
        """
        pass
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否暂停成功
        """
        pass
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否停止成功
        """
        pass
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskInfo: 任务信息
        """
        pass
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskInfo]:
        """列出任务
        
        Args:
            status: 过滤状态
            
        Returns:
            List[TaskInfo]: 任务列表
        """
        pass
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数
        
        Args:
            event: 事件名称
            callback: 回调函数
        """
        pass
```

#### 使用示例

```python
from src.core.task_manager import TaskManager, TaskConfig, TaskPriority

# 初始化任务管理器
task_manager = TaskManager(max_concurrent=2)

# 创建任务配置
config = TaskConfig(
    name="日常任务",
    description="执行每日任务",
    priority=TaskPriority.NORMAL,
    max_retries=3,
    timeout=300.0,
    parameters={
        'task_type': 'daily',
        'auto_claim': True
    }
)

# 创建任务
task_id = task_manager.create_task(config)
print(f"创建任务: {task_id}")

# 启动任务
if task_manager.start_task(task_id):
    print("任务启动成功")

# 监控任务状态
def on_task_completed(task_id: str, result: dict):
    print(f"任务 {task_id} 完成: {result}")

task_manager.register_callback('task_completed', on_task_completed)

# 获取任务信息
task_info = task_manager.get_task_info(task_id)
if task_info:
    print(f"任务状态: {task_info.status}")
    print(f"进度: {task_info.progress:.1%}")
```

### 4. 事件总线模块 (EventBus)

#### 类定义

```python
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    """事件"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str

class EventBus:
    """事件总线"""
    
    def __init__(self):
        """初始化事件总线"""
        pass
    
    def subscribe(self, event_name: str, callback: Callable[[Event], None],
                 priority: int = 0) -> str:
        """订阅事件
        
        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 优先级（数字越大优先级越高）
            
        Returns:
            str: 订阅ID
        """
        pass
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 是否取消成功
        """
        pass
    
    def publish(self, event_name: str, data: Dict[str, Any], 
               source: str = "unknown") -> bool:
        """发布事件
        
        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件源
            
        Returns:
            bool: 是否发布成功
        """
        pass
    
    def publish_async(self, event_name: str, data: Dict[str, Any],
                     source: str = "unknown") -> None:
        """异步发布事件
        
        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件源
        """
        pass
```

#### 使用示例

```python
from src.services.event_bus import EventBus, Event

# 初始化事件总线
event_bus = EventBus()

# 订阅事件
def on_game_detected(event: Event):
    print(f"游戏检测到: {event.data}")

def on_task_started(event: Event):
    print(f"任务开始: {event.data['task_id']}")

# 注册事件处理器
game_sub = event_bus.subscribe('game_detected', on_game_detected)
task_sub = event_bus.subscribe('task_started', on_task_started)

# 发布事件
event_bus.publish('game_detected', {
    'window_title': '崩坏：星穹铁道',
    'window_rect': (0, 0, 1920, 1080)
}, source='GameDetector')

event_bus.publish('task_started', {
    'task_id': 'task_001',
    'task_name': '日常任务'
}, source='TaskManager')

# 取消订阅
event_bus.unsubscribe(game_sub)
```

### 5. 配置管理模块 (ConfigManager)

#### 类定义

```python
from typing import Any, Dict, Optional, Union
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Union[str, Path]):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        pass
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            bool: 是否设置成功
        """
        pass
    
    def load_config(self, filename: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            filename: 配置文件名
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        pass
    
    def save_config(self, filename: str, config: Dict[str, Any]) -> bool:
        """保存配置文件
        
        Args:
            filename: 配置文件名
            config: 配置字典
            
        Returns:
            bool: 是否保存成功
        """
        pass
    
    def reload(self) -> bool:
        """重新加载配置
        
        Returns:
            bool: 是否重新加载成功
        """
        pass
```

#### 使用示例

```python
from src.config.app_config import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager('config')

# 获取配置
game_path = config_manager.get('game.path', 'C:\\Games\\StarRail')
detection_threshold = config_manager.get('detection.threshold', 0.8)

# 设置配置
config_manager.set('game.resolution', '1920x1080')
config_manager.set('automation.delay', 500)

# 加载特定配置文件
game_config = config_manager.load_config('game_settings.json')
automation_config = config_manager.load_config('automation_config.json')

# 保存配置
new_config = {
    'version': '1.0.0',
    'debug': False,
    'logging': {
        'level': 'INFO',
        'file': 'app.log'
    }
}
config_manager.save_config('app_settings.json', new_config)
```

## 接口规范

### 1. 返回值规范

所有API接口应遵循统一的返回值格式：

```python
@dataclass
class ApiResponse:
    """API响应"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    code: int = 0
    timestamp: float = field(default_factory=time.time)
```

### 2. 异常处理规范

```python
class XingTieException(Exception):
    """基础异常类"""
    pass

class GameDetectionError(XingTieException):
    """游戏检测异常"""
    pass

class OperationError(XingTieException):
    """操作异常"""
    pass

class ConfigurationError(XingTieException):
    """配置异常"""
    pass

class TaskError(XingTieException):
    """任务异常"""
    pass
```

### 3. 日志规范

```python
import logging
from typing import Any

class ApiLogger:
    """API日志记录器"""
    
    @staticmethod
    def log_api_call(func_name: str, args: tuple, kwargs: dict):
        """记录API调用"""
        logging.info(f"API调用: {func_name}, 参数: {args}, {kwargs}")
    
    @staticmethod
    def log_api_result(func_name: str, result: Any, duration: float):
        """记录API结果"""
        logging.info(f"API结果: {func_name}, 耗时: {duration:.3f}s")
    
    @staticmethod
    def log_api_error(func_name: str, error: Exception):
        """记录API错误"""
        logging.error(f"API错误: {func_name}, 异常: {error}")
```

## 使用示例

### 完整的自动化流程示例

```python
import asyncio
from src.core.game_detector import GameDetector
from src.core.game_operator import GameOperator
from src.core.task_manager import TaskManager, TaskConfig, TaskPriority
from src.services.event_bus import EventBus
from src.config.app_config import ConfigManager

async def main():
    # 初始化组件
    config_manager = ConfigManager('config')
    event_bus = EventBus()
    
    # 初始化游戏检测器
    detector_config = {
        'threshold': config_manager.get('detection.threshold', 0.8),
        'timeout': config_manager.get('detection.timeout', 30),
        'template_path': 'assets/templates/'
    }
    detector = GameDetector(detector_config)
    
    # 初始化游戏操作器
    operator = GameOperator(detector)
    
    # 初始化任务管理器
    task_manager = TaskManager(max_concurrent=2)
    
    # 查找游戏窗口
    print("正在查找游戏窗口...")
    window = detector.find_game_window()
    if not window:
        print("未找到游戏窗口")
        return
    
    print(f"找到游戏窗口: {window.title}")
    
    # 创建自动化任务
    task_config = TaskConfig(
        name="每日任务自动化",
        description="自动完成每日任务",
        priority=TaskPriority.NORMAL,
        max_retries=3,
        timeout=600.0,
        parameters={
            'tasks': ['daily_training', 'assignment', 'mail'],
            'auto_claim': True
        }
    )
    
    # 创建并启动任务
    task_id = task_manager.create_task(task_config)
    print(f"创建任务: {task_id}")
    
    if task_manager.start_task(task_id):
        print("任务启动成功")
        
        # 监控任务进度
        while True:
            task_info = task_manager.get_task_info(task_id)
            if task_info:
                print(f"任务状态: {task_info.status}, 进度: {task_info.progress:.1%}")
                
                if task_info.status in ['completed', 'failed', 'cancelled']:
                    break
            
            await asyncio.sleep(5)
    
    print("自动化流程完成")

if __name__ == "__main__":
    asyncio.run(main())
```

### 自定义任务开发示例

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.core.game_operator import GameOperator
from src.core.task_manager import TaskStatus

class BaseTask(ABC):
    """任务基类"""
    
    def __init__(self, operator: GameOperator, config: Dict[str, Any]):
        self.operator = operator
        self.config = config
        self.status = TaskStatus.PENDING
        self.progress = 0.0
    
    @abstractmethod
    async def execute(self) -> bool:
        """执行任务"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取任务描述"""
        pass

class DailyTaskAutomation(BaseTask):
    """每日任务自动化"""
    
    async def execute(self) -> bool:
        """执行每日任务"""
        try:
            self.status = TaskStatus.RUNNING
            
            # 步骤1: 打开任务界面
            self.progress = 0.1
            result = self.operator.click_template('task_button')
            if not result.success:
                return False
            
            # 步骤2: 领取奖励
            self.progress = 0.5
            result = self.operator.click_template('claim_all_button')
            if not result.success:
                return False
            
            # 步骤3: 完成任务
            self.progress = 0.8
            # ... 具体任务逻辑
            
            self.progress = 1.0
            self.status = TaskStatus.COMPLETED
            return True
            
        except Exception as e:
            self.status = TaskStatus.FAILED
            raise TaskError(f"每日任务执行失败: {e}")
    
    def get_description(self) -> str:
        return "自动完成每日任务并领取奖励"

# 注册自定义任务
task_registry = {
    'daily_task': DailyTaskAutomation,
    # 其他任务类型...
}
```

## 错误处理

### 异常层次结构

```python
XingTieException
├── GameDetectionError
│   ├── WindowNotFoundError
│   ├── TemplateNotFoundError
│   └── ScreenshotError
├── OperationError
│   ├── ClickError
│   ├── KeyboardError
│   └── DragError
├── TaskError
│   ├── TaskTimeoutError
│   ├── TaskCancelledError
│   └── TaskConfigError
└── ConfigurationError
    ├── ConfigFileError
    ├── ConfigValidationError
    └── ConfigPermissionError
```

### 错误处理最佳实践

```python
from src.exceptions import GameDetectionError, OperationError
import logging

def safe_operation(func):
    """安全操作装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GameDetectionError as e:
            logging.error(f"游戏检测错误: {e}")
            return None
        except OperationError as e:
            logging.error(f"操作错误: {e}")
            return None
        except Exception as e:
            logging.error(f"未知错误: {e}")
            return None
    return wrapper

@safe_operation
def click_with_retry(operator: GameOperator, template: str, max_retries: int = 3):
    """带重试的点击操作"""
    for i in range(max_retries):
        try:
            result = operator.click_template(template)
            if result.success:
                return result
        except Exception as e:
            if i == max_retries - 1:
                raise OperationError(f"点击失败，已重试{max_retries}次: {e}")
            time.sleep(1)
    return None
```

## 扩展开发

### 插件系统

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class Plugin(ABC):
    """插件基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本"""
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理插件"""
        pass

class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
    
    def load_plugin(self, plugin: Plugin, context: Dict[str, Any]) -> bool:
        """加载插件"""
        try:
            if plugin.initialize(context):
                self.plugins[plugin.get_name()] = plugin
                return True
        except Exception as e:
            logging.error(f"插件加载失败: {e}")
        return False
    
    def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        if name in self.plugins:
            try:
                self.plugins[name].cleanup()
                del self.plugins[name]
                return True
            except Exception as e:
                logging.error(f"插件卸载失败: {e}")
        return False
```

### 自定义模板检测器

```python
class CustomTemplateDetector:
    """自定义模板检测器"""
    
    def __init__(self, detector: GameDetector):
        self.detector = detector
        self.custom_templates = {}
    
    def register_template(self, name: str, template_data: bytes, 
                         threshold: float = 0.8):
        """注册自定义模板"""
        self.custom_templates[name] = {
            'data': template_data,
            'threshold': threshold
        }
    
    def detect_custom(self, name: str) -> DetectionResult:
        """检测自定义模板"""
        if name not in self.custom_templates:
            raise TemplateNotFoundError(f"模板 {name} 未注册")
        
        template_info = self.custom_templates[name]
        # 使用自定义检测逻辑
        return self.detector.detect_template(name)
```

---

**注意**: 本API文档描述的是核心接口规范，具体实现可能会根据项目发展进行调整。建议在使用前查看最新的代码实现和文档更新。