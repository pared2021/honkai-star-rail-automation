"""自动化服务接口

定义自动化相关的业务逻辑接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class IAutomationService(ABC):
    """自动化服务接口
    
    定义自动化相关的业务操作。
    """
    
    @abstractmethod
    async def create_automation_rule(self, rule_data: Dict[str, Any]) -> Any:
        """创建自动化规则
        
        Args:
            rule_data: 规则数据
            
        Returns:
            创建的规则对象
        """
        pass
    
    @abstractmethod
    async def get_automation_rule(self, rule_id: str) -> Optional[Any]:
        """获取自动化规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_automation_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Optional[Any]:
        """更新自动化规则
        
        Args:
            rule_id: 规则ID
            rule_data: 更新的规则数据
            
        Returns:
            更新后的规则对象
        """
        pass
    
    @abstractmethod
    async def delete_automation_rule(self, rule_id: str) -> bool:
        """删除自动化规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def enable_automation_rule(self, rule_id: str) -> bool:
        """启用自动化规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否启用成功
        """
        pass
    
    @abstractmethod
    async def disable_automation_rule(self, rule_id: str) -> bool:
        """禁用自动化规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否禁用成功
        """
        pass
    
    @abstractmethod
    async def execute_automation_rule(self, rule_id: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """执行自动化规则
        
        Args:
            rule_id: 规则ID
            context: 执行上下文
            
        Returns:
            是否执行成功
        """
        pass
    
    @abstractmethod
    async def list_automation_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """列出自动化规则
        
        Args:
            filters: 过滤条件
            
        Returns:
            规则列表
        """
        pass
    
    @abstractmethod
    async def get_active_rules(self) -> List[Any]:
        """获取活跃的自动化规则
        
        Returns:
            活跃规则列表
        """
        pass
    
    @abstractmethod
    async def validate_rule_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """验证规则条件
        
        Args:
            condition: 规则条件
            context: 验证上下文
            
        Returns:
            条件是否满足
        """
        pass
    
    @abstractmethod
    async def execute_rule_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行规则动作
        
        Args:
            action: 规则动作
            context: 执行上下文
            
        Returns:
            是否执行成功
        """
        pass
    
    @abstractmethod
    async def get_rule_execution_history(self, rule_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取规则执行历史
        
        Args:
            rule_id: 规则ID
            limit: 限制返回数量
            
        Returns:
            执行历史列表
        """
        pass
    
    @abstractmethod
    async def schedule_rule_execution(self, rule_id: str, schedule_time: datetime) -> bool:
        """调度规则执行
        
        Args:
            rule_id: 规则ID
            schedule_time: 调度时间
            
        Returns:
            是否调度成功
        """
        pass
    
    @abstractmethod
    async def get_automation_statistics(self) -> Dict[str, Any]:
        """获取自动化统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def test_automation_rule(self, rule_data: Dict[str, Any], test_context: Dict[str, Any]) -> Dict[str, Any]:
        """测试自动化规则
        
        Args:
            rule_data: 规则数据
            test_context: 测试上下文
            
        Returns:
            测试结果
        """
        pass