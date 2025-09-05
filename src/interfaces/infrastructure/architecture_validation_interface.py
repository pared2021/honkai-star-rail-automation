"""架构验证接口

定义架构验证的抽象接口，用于验证架构一致性和质量。
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from pathlib import Path

from .architecture_validation_types import (
    ValidationResult,
    DependencyInfo,
    ModuleInfo,
    ArchitectureMetrics
)


class IArchitectureValidator(ABC):
    """架构验证器接口"""
    
    @abstractmethod
    def validate_project(self, project_path: Path) -> List[ValidationResult]:
        """验证整个项目
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_module(self, module_path: Path) -> List[ValidationResult]:
        """验证单个模块
        
        Args:
            module_path: 模块路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_dependencies(self, project_path: Path) -> List[ValidationResult]:
        """验证依赖关系
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_layer_architecture(self, project_path: Path) -> List[ValidationResult]:
        """验证分层架构
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_solid_principles(self, project_path: Path) -> List[ValidationResult]:
        """验证SOLID原则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def detect_circular_dependencies(self, project_path: Path) -> List[DependencyInfo]:
        """检测循环依赖
        
        Args:
            project_path: 项目路径
            
        Returns:
            循环依赖列表
        """
        pass
    
    @abstractmethod
    def analyze_coupling(self, project_path: Path) -> Dict[str, float]:
        """分析耦合度
        
        Args:
            project_path: 项目路径
            
        Returns:
            模块耦合度字典
        """
        pass
    
    @abstractmethod
    def analyze_cohesion(self, project_path: Path) -> Dict[str, float]:
        """分析内聚度
        
        Args:
            project_path: 项目路径
            
        Returns:
            模块内聚度字典
        """
        pass
    
    @abstractmethod
    def calculate_metrics(self, project_path: Path) -> ArchitectureMetrics:
        """计算架构指标
        
        Args:
            project_path: 项目路径
            
        Returns:
            架构指标
        """
        pass
    
    @abstractmethod
    def get_module_info(self, project_path: Path) -> List[ModuleInfo]:
        """获取模块信息
        
        Args:
            project_path: 项目路径
            
        Returns:
            模块信息列表
        """
        pass
    
    @abstractmethod
    def generate_dependency_graph(self, project_path: Path) -> Dict[str, Any]:
        """生成依赖关系图
        
        Args:
            project_path: 项目路径
            
        Returns:
            依赖关系图数据
        """
        pass
    
    @abstractmethod
    def set_validation_rules(self, rules: Dict[str, Any]) -> None:
        """设置验证规则
        
        Args:
            rules: 验证规则配置
        """
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """获取验证规则
        
        Returns:
            验证规则配置
        """
        pass


class IDependencyAnalyzer(ABC):
    """依赖分析器接口"""
    
    @abstractmethod
    def analyze_dependencies(self, project_path: Path) -> List[DependencyInfo]:
        """分析项目依赖
        
        Args:
            project_path: 项目路径
            
        Returns:
            依赖信息列表
        """
        pass
    
    @abstractmethod
    def find_circular_dependencies(self, dependencies: List[DependencyInfo]) -> List[List[str]]:
        """查找循环依赖
        
        Args:
            dependencies: 依赖信息列表
            
        Returns:
            循环依赖路径列表
        """
        pass
    
    @abstractmethod
    def calculate_dependency_depth(self, module: str, dependencies: List[DependencyInfo]) -> int:
        """计算依赖深度
        
        Args:
            module: 模块名称
            dependencies: 依赖信息列表
            
        Returns:
            依赖深度
        """
        pass
    
    @abstractmethod
    def get_dependency_tree(self, module: str, dependencies: List[DependencyInfo]) -> Dict[str, Any]:
        """获取依赖树
        
        Args:
            module: 模块名称
            dependencies: 依赖信息列表
            
        Returns:
            依赖树结构
        """
        pass
    
    @abstractmethod
    def suggest_dependency_optimization(self, dependencies: List[DependencyInfo]) -> List[str]:
        """建议依赖优化
        
        Args:
            dependencies: 依赖信息列表
            
        Returns:
            优化建议列表
        """
        pass


class ILayerValidator(ABC):
    """分层验证器接口"""
    
    @abstractmethod
    def validate_layer_separation(self, project_path: Path) -> List[ValidationResult]:
        """验证层级分离
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_dependency_direction(self, project_path: Path) -> List[ValidationResult]:
        """验证依赖方向
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def get_layer_mapping(self) -> Dict[str, ArchitectureLayer]:
        """获取层级映射
        
        Returns:
            路径到层级的映射
        """
        pass
    
    @abstractmethod
    def set_layer_mapping(self, mapping: Dict[str, ArchitectureLayer]) -> None:
        """设置层级映射
        
        Args:
            mapping: 路径到层级的映射
        """
        pass
    
    @abstractmethod
    def validate_layer_rules(self, project_path: Path) -> List[ValidationResult]:
        """验证层级规则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass


class ISOLIDValidator(ABC):
    """SOLID原则验证器接口"""
    
    @abstractmethod
    def validate_single_responsibility(self, project_path: Path) -> List[ValidationResult]:
        """验证单一职责原则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_open_closed(self, project_path: Path) -> List[ValidationResult]:
        """验证开闭原则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_liskov_substitution(self, project_path: Path) -> List[ValidationResult]:
        """验证里氏替换原则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_interface_segregation(self, project_path: Path) -> List[ValidationResult]:
        """验证接口隔离原则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass
    
    @abstractmethod
    def validate_dependency_inversion(self, project_path: Path) -> List[ValidationResult]:
        """验证依赖倒置原则
        
        Args:
            project_path: 项目路径
            
        Returns:
            验证结果列表
        """
        pass


class IArchitectureReporter(ABC):
    """架构报告器接口"""
    
    @abstractmethod
    def generate_report(self, 
                       validation_results: List[ValidationResult],
                       metrics: ArchitectureMetrics,
                       output_path: Path) -> None:
        """生成架构报告
        
        Args:
            validation_results: 验证结果
            metrics: 架构指标
            output_path: 输出路径
        """
        pass
    
    @abstractmethod
    def generate_html_report(self, 
                            validation_results: List[ValidationResult],
                            metrics: ArchitectureMetrics,
                            output_path: Path) -> None:
        """生成HTML报告
        
        Args:
            validation_results: 验证结果
            metrics: 架构指标
            output_path: 输出路径
        """
        pass
    
    @abstractmethod
    def generate_json_report(self, 
                            validation_results: List[ValidationResult],
                            metrics: ArchitectureMetrics,
                            output_path: Path) -> None:
        """生成JSON报告
        
        Args:
            validation_results: 验证结果
            metrics: 架构指标
            output_path: 输出路径
        """
        pass
    
    @abstractmethod
    def generate_summary(self, metrics: ArchitectureMetrics) -> str:
        """生成摘要
        
        Args:
            metrics: 架构指标
            
        Returns:
            摘要文本
        """
        pass