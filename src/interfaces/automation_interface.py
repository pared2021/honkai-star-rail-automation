"""自动化相关接口定义.

提供统一的接口规范，确保接口定义与实现一致。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple


class IAutomationController(ABC):
    """自动化控制器接口."""
    
    @abstractmethod
    def start_automation(self) -> bool:
        """启动自动化.
        
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def stop_automation(self) -> bool:
        """停止自动化.
        
        Returns:
            bool: 停止成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def get_automation_status(self) -> str:
        """获取自动化状态.
        
        Returns:
            str: 自动化状态（running/stopped/error）
        """
        pass
    
    @abstractmethod
    def get_available_tasks(self) -> List[str]:
        """获取可用任务列表.
        
        Returns:
            List[str]: 可用任务名称列表
        """
        pass


class IGameDetector(ABC):
    """游戏检测器接口."""
    
    @abstractmethod
    def detect_game_window(self) -> Optional[Dict[str, Any]]:
        """检测游戏窗口.
        
        Returns:
            Optional[Dict[str, Any]]: 游戏窗口信息，未找到返回None
        """
        pass
    
    @abstractmethod
    def is_game_running(self) -> bool:
        """检查游戏是否运行.
        
        Returns:
            bool: 游戏是否正在运行
        """
        pass
    
    @abstractmethod
    def capture_screen(self) -> Optional[bytes]:
        """截取游戏画面.
        
        Returns:
            Optional[bytes]: 截图数据，失败返回None
        """
        pass
    
    @abstractmethod
    def find_template(self, template_path: str, threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        """模板匹配查找UI元素.
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
            
        Returns:
            Optional[Dict[str, Any]]: 匹配结果，未找到返回None
        """
        pass
    
    @abstractmethod
    def get_game_status(self) -> Dict[str, Any]:
        """获取游戏状态.
        
        Returns:
            Dict[str, Any]: 游戏状态信息
        """
        pass


class ITaskManager(ABC):
    """任务管理器接口."""
    
    @abstractmethod
    def create_task(self, task_config: Dict[str, Any]) -> str:
        """创建任务.
        
        Args:
            task_config: 任务配置
            
        Returns:
            str: 任务ID
        """
        pass
    
    @abstractmethod
    def start_task(self, task_id: str) -> bool:
        """启动任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def stop_task(self, task_id: str) -> bool:
        """停止任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 停止成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> str:
        """获取任务状态.
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 任务状态
        """
        pass
    
    @abstractmethod
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务.
        
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        pass


class IMetricsCollector(ABC):
    """指标收集器接口."""
    
    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录仪表盘指标.
        
        Args:
            name: 指标名称
            value: 指标值
            tags: 标签
        """
        pass
    
    @abstractmethod
    def record_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """记录计数器指标.
        
        Args:
            name: 指标名称
            value: 增量值
            tags: 标签
        """
        pass
    
    @abstractmethod
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录直方图指标.
        
        Args:
            name: 指标名称
            value: 指标值
            tags: 标签
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标.
        
        Returns:
            Dict[str, Any]: 指标数据
        """
        pass